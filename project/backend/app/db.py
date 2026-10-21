from collections.abc import Iterator
from datetime import datetime
from functools import lru_cache
from typing import ClassVar

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
