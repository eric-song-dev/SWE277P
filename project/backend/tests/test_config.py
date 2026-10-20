import pytest
from pydantic import ValidationError

from app.config import Settings


def test_invalid_secret_key_is_rejected(monkeypatch):
    monkeypatch.setenv("HUB_SECRET_KEY", "not-a-fernet-key")
    with pytest.raises(ValidationError, match="Fernet"):
        Settings()
