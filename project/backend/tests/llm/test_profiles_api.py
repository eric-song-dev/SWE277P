import json

import pytest
from sqlalchemy import select

from app.config import Settings
from app.errors import HubError
from app.llm import service
from app.llm.crypto import decrypt_api_key
from app.llm.models import LlmProfile

KEY = "sk-test-1234567890abcd"


def make(client, name="OpenAI", preset="openai", **extra):
    body = {"name": name, "preset": preset, "model": "gpt-4.1-mini", "api_key": KEY, **extra}
    return client.post("/api/llm-profiles", json=body)


def test_key_never_returned(client):
    created = make(client).json()
    patched = client.patch(f"/api/llm-profiles/{created['id']}", json={"model": "gpt-4.1"})
    for body in (created, client.get("/api/llm-profiles").json(), patched.json()):
        text = json.dumps(body)
        assert KEY not in text and "ciphertext" not in text
    assert created["api_key_hint"] == "sk-…abcd" and created["has_api_key"] is True
    assert created["base_url"] == "https://api.openai.com/v1"


def test_patch_without_key_keeps_key(client, db_session):
    created = make(client).json()
    client.patch(f"/api/llm-profiles/{created['id']}", json={"model": "gpt-4.1"})
    profile, key = service.get_profile_with_key(db_session, created["id"])
    assert key == KEY and profile.model == "gpt-4.1"
    client.patch(f"/api/llm-profiles/{created['id']}", json={"api_key": "sk-other-9999999999zzzz"})
    db_session.expire_all()
    assert service.get_profile_with_key(db_session, created["id"])[1] == "sk-other-9999999999zzzz"


def test_patch_sets_updated_at(client, db_session):
    created = make(client).json()
    before = db_session.get(LlmProfile, created["id"]).updated_at
    client.patch(f"/api/llm-profiles/{created['id']}", json={"model": "x"})
    db_session.expire_all()
    assert db_session.get(LlmProfile, created["id"]).updated_at > before


def test_preset_defaults(client):
    z = make(client, "Z", "zotgpt", base_url="https://zotgpt.example/v1").json()
    o = make(client, "O", "openai").json()
    assert (z["share_results_with_llm"], o["share_results_with_llm"]) == (True, False)
    explicit = make(client, "E", "openai", share_results_with_llm=True).json()
    assert explicit["share_results_with_llm"] is True


def test_custom_requires_base_url(client):
    res = make(client, "C", "custom")
    assert res.status_code == 422 and res.json()["error"]["code"] == "validation_error"
    assert KEY not in res.text


def test_patch_revalidates_merged_result(client):
    created = make(client).json()
    res = client.patch(f"/api/llm-profiles/{created['id']}", json={"preset": "custom"})
    assert res.status_code == 422 and res.json()["error"]["code"] == "validation_error"
    ok = client.patch(
        f"/api/llm-profiles/{created['id']}",
        json={"preset": "custom", "base_url": "https://llm.example/v1"},
    )
    assert ok.status_code == 200 and ok.json()["base_url"] == "https://llm.example/v1"


def test_duplicate_name_conflict(client):
    make(client)
    res = make(client)
    assert res.status_code == 409 and res.json()["error"]["code"] == "profile_name_taken"


def test_first_profile_is_default_and_switching(client):
    a = make(client, "A").json()
    b = make(client, "B").json()
    assert (a["is_default"], b["is_default"]) == (True, False)
    res = client.post(f"/api/llm-profiles/{b['id']}/default")
    assert res.status_code == 200 and res.json()["is_default"] is True
    listed = client.get("/api/llm-profiles").json()
    assert [p["name"] for p in listed if p["is_default"]] == ["B"]
    assert client.post("/api/llm-profiles/999/default").status_code == 404


def test_delete_default_promotes_oldest(client):
    a = make(client, "A").json()
    b = make(client, "B").json()
    c = make(client, "C").json()
    assert client.delete(f"/api/llm-profiles/{a['id']}").status_code == 204
    listed = client.get("/api/llm-profiles").json()
    assert [p["name"] for p in listed if p["is_default"]] == ["B"]
    assert client.delete(f"/api/llm-profiles/{c['id']}").status_code == 204
    assert client.delete(f"/api/llm-profiles/{b['id']}").status_code == 204
    assert client.get("/api/llm-profiles").json() == []
    assert client.delete("/api/llm-profiles/999").status_code == 404


def test_fake_preset_hidden_unless_enabled(client, monkeypatch):
    from app.config import get_settings

    keys = [p["key"] for p in client.get("/api/llm-profiles/presets").json()]
    assert keys == ["zotgpt", "openai", "deepseek", "custom"]
    res = client.post("/api/llm-profiles", json={"name": "F", "preset": "fake", "model": "m"})
    assert res.status_code == 422
    monkeypatch.setenv("HUB_ENABLE_FAKE_LLM", "true")
    get_settings.cache_clear()
    try:
        keys = [p["key"] for p in client.get("/api/llm-profiles/presets").json()]
        assert keys[-1] == "fake"
        res = client.post("/api/llm-profiles", json={"name": "F", "preset": "fake", "model": "m"})
        assert res.status_code == 201 and res.json()["has_api_key"] is False
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()


def test_fake_profile_needs_no_key(db_session, user, monkeypatch):
    from app.llm.schemas import LlmProfileIn

    settings = Settings(hub_enable_fake_llm=True)
    p = service.create_profile(
        db_session, LlmProfileIn(name="F", preset="fake", model="m"), user, settings
    )
    assert service.get_profile_with_key(db_session, p.id)[1] == ""


def test_get_profile_with_key_errors(db_session, user):
    with pytest.raises(HubError) as e:
        service.get_profile_with_key(db_session, None)
    assert (e.value.code, e.value.status_code) == ("profile_not_found", 404)
    from app.llm.schemas import LlmProfileIn

    service.create_profile(db_session, LlmProfileIn(name="N", preset="openai", model="m"), user)
    with pytest.raises(HubError) as e:
        service.get_profile_with_key(db_session, None)
    assert (e.value.code, e.value.status_code) == ("profile_missing_key", 409)


def seed_settings(**kw):
    base = {
        "llm_seed_name": "DeepSeek",
        "llm_seed_preset": "deepseek",
        "llm_seed_model": "deepseek-chat",
        "llm_seed_api_key": KEY,
    }
    return Settings(**{**base, **kw})


def test_seed_profile_from_env(db_session):
    service.seed_profile_from_env(db_session, seed_settings())
    rows = db_session.scalars(select(LlmProfile)).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.name == "DeepSeek" and row.base_url == "https://api.deepseek.com"
    assert row.is_default and row.created_by is not None
    assert KEY.encode() not in row.api_key_ciphertext
    assert decrypt_api_key(row.api_key_ciphertext) == KEY
    service.seed_profile_from_env(db_session, seed_settings())
    assert len(db_session.scalars(select(LlmProfile)).all()) == 1


def test_seed_skipped_without_name_or_key(db_session):
    service.seed_profile_from_env(db_session, seed_settings(llm_seed_api_key=""))
    service.seed_profile_from_env(db_session, seed_settings(llm_seed_name=""))
    service.seed_profile_from_env(db_session, Settings())
    assert db_session.scalars(select(LlmProfile)).all() == []


def test_seed_share_results_parsed(db_session):
    service.seed_profile_from_env(db_session, seed_settings(llm_seed_share_results="true"))
    assert db_session.scalars(select(LlmProfile)).one().share_results_with_llm is True


def test_patch_rejects_unknown_or_unavailable_preset(client):
    created = make(client).json()
    for preset in ("bogus", "fake"):
        res = client.patch(f"/api/llm-profiles/{created['id']}", json={"preset": preset})
        assert res.status_code == 422 and res.json()["error"]["code"] == "validation_error"
