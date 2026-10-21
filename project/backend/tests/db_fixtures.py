import os
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from alembic import command

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DB = "hub_test"
HUB_TABLES = ", ".join(
    f"hub.{t}"
    for t in (
        "data_quality_flag", "attendance", "person_identifier", "person", "import_file",
        "event", "app_user",
    )
)  # fmt: skip


def test_url(url: str) -> str:
    """Return `url` pointed at the hub_test database."""
    return make_url(url).set(database=TEST_DB).render_as_string(hide_password=False)


@pytest.fixture(scope="session")
def test_database():
    admin = create_engine(os.environ["TEST_ADMIN_DATABASE_URL"], isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB} OWNER hub_app"))
    admin.dispose()

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"].replace("%", "%%"))
    command.upgrade(cfg, "head")
    return TEST_DB


@pytest.fixture(scope="session")
def _app_engine(test_database):
    engine = create_engine(os.environ["DATABASE_URL"])
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(_app_engine):
    with _app_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {HUB_TABLES} RESTART IDENTITY CASCADE"))
        conn.execute(
            text(
                "INSERT INTO hub.app_user (username, display_name) VALUES ('local', 'GPSRC Staff')"
            )
        )
    with Session(_app_engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def chatbot_engine(test_database):
    engine = create_engine(os.environ["CHATBOT_DATABASE_URL"])
    yield engine
    engine.dispose()
