from sqlalchemy import create_engine, text

from alembic import context
from app.auth import models as _auth  # noqa: F401
from app.config import get_settings
from app.dataset import models as _dataset  # noqa: F401
from app.db import SCHEMA, Base
from app.events import models as _events  # noqa: F401
from app.imports import models as _imports  # noqa: F401
from app.quality import models as _quality  # noqa: F401

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    # Tests point Alembic at hub_test through the config option.
    return config.get_main_option("sqlalchemy.url") or get_settings().database_url


def run_migrations_online() -> None:
    engine = create_engine(_url())
    with engine.connect() as connection:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
