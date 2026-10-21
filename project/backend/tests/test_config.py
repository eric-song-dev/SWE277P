import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError

from app.config import FERNET_HELP, Settings


def test_invalid_secret_key_is_rejected(monkeypatch):
    monkeypatch.setenv("HUB_SECRET_KEY", "not-a-fernet-key")
    with pytest.raises(ValidationError, match="Fernet"):
        Settings()


SENTINEL = "bad-key-SENTINEL-1234"


def _build(**overrides):
    values = {
        "database_url": "postgresql+psycopg://u:p@localhost/db",
        "chatbot_database_url": "postgresql+psycopg://u:p@localhost/db",
        "hub_secret_key": "x",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_invalid_secret_key_value_is_never_echoed():
    with pytest.raises(ValidationError) as excinfo:
        _build(hub_secret_key=SENTINEL)
    for text in (str(excinfo.value), repr(excinfo.value)):
        assert SENTINEL not in text
        assert "hub_secret_key" in text
        assert FERNET_HELP in text


def test_invalid_setting_value_is_never_echoed():
    with pytest.raises(ValidationError) as excinfo:
        _build(
            hub_secret_key=Fernet.generate_key().decode(),
            display_row_cap="postgres://u:pw-SENTINEL-5678@h/db",
        )
    for text in (str(excinfo.value), repr(excinfo.value)):
        assert "pw-SENTINEL-5678" not in text
        assert "display_row_cap" in text
