from collections.abc import Iterator
from datetime import datetime
from functools import lru_cache
from typing import Annotated, ClassVar

from fastapi import Depends
from sqlalchemy import DateTime, MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

SCHEMA = "hub"


class Base(DeclarativeBase):
    metadata = MetaData(schema=SCHEMA)
    type_annotation_map: ClassVar[dict] = {datetime: DateTime(timezone=True)}


@lru_cache
def get_app_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_chatbot_engine() -> Engine:
    return create_engine(get_settings().chatbot_database_url, pool_pre_ping=True)


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
