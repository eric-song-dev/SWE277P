from cryptography.fernet import Fernet

from app.config import get_settings


def _fernet() -> Fernet:
    return Fernet(get_settings().hub_secret_key.get_secret_value())


def encrypt_api_key(plain: str) -> bytes:
    return _fernet().encrypt(plain.encode())


def decrypt_api_key(cipher: bytes) -> str:
    return _fernet().decrypt(cipher).decode()


def api_key_hint(plain: str) -> str:
    """A short, non-reversible label for the UI; keys under 12 characters show no part."""
    if len(plain) >= 12:
        return f"{plain[:3]}…{plain[-4:]}"
    return "…"
