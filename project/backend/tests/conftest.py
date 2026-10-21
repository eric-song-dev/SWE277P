import os
from pathlib import Path

from cryptography.fernet import Fernet
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
_file_values = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}


def _configured(name: str) -> str:
    value = os.environ.get(name) or _file_values.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set in the environment or project/.env")
    return value


def _hub_test(url: str) -> str:
    return make_url(url).set(database="hub_test").render_as_string(hide_password=False)


# Tests must never touch the dev `hub` database: point the app at hub_test.
os.environ["DATABASE_URL"] = _hub_test(_configured("DATABASE_URL"))
os.environ["CHATBOT_DATABASE_URL"] = _hub_test(_configured("CHATBOT_DATABASE_URL"))
os.environ["TEST_ADMIN_DATABASE_URL"] = _configured("TEST_ADMIN_DATABASE_URL")
os.environ["HUB_SECRET_KEY"] = Fernet.generate_key().decode()

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from tests.db_fixtures import _app_engine, chatbot_engine, db_session, test_database  # noqa: F401

get_settings.cache_clear()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app, request):
    request.getfixturevalue("db_session")  # migrates the test DB and seeds the `local` user
    return TestClient(app)


@pytest.fixture
def user(request):
    session = request.getfixturevalue("db_session")
    from sqlalchemy import select

    from app.auth.models import AppUser
    from app.auth.schemas import CurrentUser

    row = session.scalar(select(AppUser).where(AppUser.username == "local"))
    return CurrentUser(id=row.id, username=row.username, display_name=row.display_name)


@pytest.fixture
def committed_october(request):
    session = request.getfixturevalue("db_session")
    user = request.getfixturevalue("user")
    from tests.imports.helpers import commit_after_preview, sample_bytes

    name = "Bagel Breakfast - October.csv"
    summary = commit_after_preview(session, name, sample_bytes(name), user)
    session.commit()
    return summary
