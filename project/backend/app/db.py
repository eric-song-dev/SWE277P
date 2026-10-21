from collections.abc import Iterator
from datetime import datetime
from functools import lru_cache
from typing import Annotated, ClassVar

from fastapi import Depends
from sqlalchemy import DateTime, MetaData, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

SCHEMA = "hub"


class Base(DeclarativeBase):
    metadata = MetaData(schema=SCHEMA)
    type_annotation_map: ClassVar[dict] = {datetime: DateTime(timezone=True)}


@lru_cache
def get_app_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True, hide_parameters=True)


def make_chatbot_engine(url: str) -> Engine:
    """Engine for the read-only chatbot role; resets session state when a connection is returned.

    RESET ALL (not DISCARD ALL) because psycopg caches server-side prepared statements per
    connection, and DISCARD ALL would deallocate them behind its back.
    """
    engine = create_engine(url, pool_pre_ping=True)

    @event.listens_for(engine, "reset")
    def _reset_session_state(dbapi_connection, connection_record, reset_state):
        dbapi_connection.rollback()
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("RESET ALL")
            # RESET ALL leaves session-level advisory locks held; release them too.
            cursor.execute("SELECT pg_advisory_unlock_all()")
        finally:
            cursor.close()
        dbapi_connection.commit()

    return engine


@lru_cache
def get_chatbot_engine() -> Engine:
    return make_chatbot_engine(get_settings().chatbot_database_url)


SessionLocal = sessionmaker(expire_on_commit=False)


def get_session() -> Iterator[Session]:
    with SessionLocal(bind=get_app_engine()) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


# Function scope runs the commit before the response is sent, so a failed commit becomes an
# error response. Every route and get_current_user must use this alias: the dependency cache
# is keyed by scope, so mixing scopes would open two sessions per request.
SessionDep = Annotated[Session, Depends(get_session, scope="function")]
