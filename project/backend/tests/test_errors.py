from typing import Annotated

import pytest
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, StringConstraints

from app.errors import HubError, install_error_handlers

SECRET = "sk-test-0123456789abcdef"


class ProfileIn(BaseModel):
    name: str
    model: str
    api_key: Annotated[str, StringConstraints(min_length=64)]


@pytest.fixture
def probe() -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)

    @app.post("/profiles")
    def create_profile(body: ProfileIn) -> dict:
        return {}

    @app.get("/hub-error")
    def hub_error() -> dict:
        raise HubError("thing_conflict", "That thing is busy.", 409, {"thing_id": 7})

    @app.get("/crash")
    def crash() -> dict:
        raise RuntimeError(f"database password is {SECRET}")

    return app


def test_validation_error_never_echoes_submitted_values(probe):
    # `model` is missing (that error's input is the whole body) and `api_key` is too short
    # (that error's input is the key itself, with min_length in ctx).
    res = TestClient(probe).post("/profiles", json={"name": "x", "api_key": SECRET})
    assert res.status_code == 422
    assert SECRET not in res.text
    error = res.json()["error"]
    assert (error["code"], error["message"]) == ("validation_error", "Request validation failed")
    assert {tuple(e["loc"]) for e in error["details"]} == {
        ("body", "model"),
        ("body", "api_key"),
    }
    assert all(set(e) == {"loc", "msg", "type"} for e in error["details"])


def test_hub_error_uses_its_status_code_and_details(probe):
    res = TestClient(probe).get("/hub-error")
    assert res.status_code == 409
    assert res.json() == {
        "error": {
            "code": "thing_conflict",
            "message": "That thing is busy.",
            "details": {"thing_id": 7},
        }
    }


def test_unhandled_error_logs_the_type_only(probe, caplog):
    TestClient(probe, raise_server_exceptions=False).get("/crash")
    records = [r for r in caplog.records if r.name == "app.errors"]
    assert len(records) == 1
    assert "RuntimeError" in records[0].getMessage()
    assert records[0].exc_info is None
    assert SECRET not in caplog.text and "Traceback" not in caplog.text


def test_unhandled_error_is_generic_500(probe):
    res = TestClient(probe, raise_server_exceptions=False).get("/crash")
    assert res.status_code == 500
    assert res.json() == {
        "error": {"code": "internal_error", "message": "Internal server error", "details": None}
    }
    assert SECRET not in res.text


def test_unhandled_error_does_not_reraise_or_leak_into_logs(probe, caplog):
    # With raise_server_exceptions=True the client re-raises whatever escapes the app, which is
    # what uvicorn would log with a full traceback.
    res = TestClient(probe, raise_server_exceptions=True).get("/crash")
    assert res.status_code == 500
    assert res.json()["error"]["code"] == "internal_error"
    assert "RuntimeError" in caplog.text
    assert SECRET not in caplog.text and "Traceback" not in caplog.text


def test_error_after_response_started_is_logged_by_type_and_not_raised(caplog):
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/stream")
    def stream():
        def gen():
            yield "first"
            raise RuntimeError(f"late failure {SECRET}")

        return StreamingResponse(gen())

    res = TestClient(app, raise_server_exceptions=True).get("/stream")
    assert res.status_code == 200
    assert "RuntimeError" in caplog.text
    assert SECRET not in caplog.text and "Traceback" not in caplog.text
