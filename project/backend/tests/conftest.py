import os

from cryptography.fernet import Fernet

# Task 2 replaces these two placeholders with real test-database URLs.
os.environ["DATABASE_URL"] = "postgresql+psycopg://placeholder@localhost:5432/placeholder"
os.environ["CHATBOT_DATABASE_URL"] = "postgresql+psycopg://placeholder@localhost:5432/placeholder"
os.environ["HUB_SECRET_KEY"] = Fernet.generate_key().decode()

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app

get_settings.cache_clear()


@pytest.fixture
def client():
    return TestClient(create_app())
