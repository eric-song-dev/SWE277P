from app.llm.crypto import api_key_hint, decrypt_api_key, encrypt_api_key

KEY = "sk-test-1234567890abcd"


def test_roundtrip():
    cipher = encrypt_api_key(KEY)
    assert isinstance(cipher, bytes)
    assert KEY.encode() not in cipher
    assert decrypt_api_key(cipher) == KEY


def test_hint():
    assert api_key_hint(KEY) == "sk-…abcd"
    assert api_key_hint("short") == "…"
    assert api_key_hint("a" * 11) == "…"
    assert api_key_hint("abcdefghijkl") == "abc…ijkl"
