import httpx
import pytest
from langchain_openai import ChatOpenAI
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
    UnprocessableEntityError,
)

from app.config import Settings
from app.llm.errors import is_response_format_unsupported, map_llm_error
from app.llm.factory import build_chat_model, json_mode_kwargs
from app.llm.fake import ScriptedChatModel
from app.llm.models import LlmProfile
from app.llm.probe import probe_profile
from tests.llm.openai_mock import chat_reply, error_reply, mock_openai, models_reply, request_json

KEY = "sk-x-secret-123456"
REQ = httpx.Request("POST", "https://x.test/v1/chat/completions")


@pytest.fixture
def settings():
    return Settings()


@pytest.fixture
def profile_openai():
    return LlmProfile(
        name="p", preset="openai", base_url="https://x.test/v1", model="m", is_default=False
    )


def handler(*, reject_format=False, status=None, models=True):
    def h(req: httpx.Request) -> httpx.Response:
        if req.url.path.endswith("/models"):
            return models_reply("b-model", "a-model") if models else error_reply(404, "no")
        if status:
            return error_reply(status, f"bad {KEY}")
        if reject_format and "response_format" in request_json(req):
            return error_reply(400, "response_format is not supported")
        return chat_reply('{"ok": true}')

    return h


async def test_probe_detects_json_mode(profile_openai, settings):
    r = await probe_profile(
        profile_openai, KEY, settings=settings, http_async_client=mock_openai(handler())
    )
    assert r.ok and r.json_mode is True and r.models == ["a-model", "b-model"]


async def test_probe_falls_back_when_response_format_rejected(profile_openai, settings):
    client = mock_openai(handler(reject_format=True))
    r = await probe_profile(profile_openai, KEY, settings=settings, http_async_client=client)
    assert r.ok and r.json_mode is False


async def test_probe_reports_auth_error(profile_openai, settings):
    client = mock_openai(handler(status=401))
    r = await probe_profile(profile_openai, KEY, settings=settings, http_async_client=client)
    assert not r.ok and "API key" in r.error and KEY not in r.error and r.json_mode is None


async def test_probe_models_listing_is_best_effort(profile_openai, settings):
    client = mock_openai(handler(models=False))
    r = await probe_profile(profile_openai, KEY, settings=settings, http_async_client=client)
    assert r.ok and r.models == []


async def test_probe_fake_preset_makes_no_network_call(settings):
    fake = LlmProfile(name="f", preset="fake", base_url="", model="demo", is_default=False)
    r = await probe_profile(fake, "", settings=settings)
    assert r.ok and r.json_mode is True and r.models == []


def _status_exc(cls, status):
    return cls("boom", response=httpx.Response(status, request=REQ), body=None)


@pytest.mark.parametrize(
    ("exc", "code"),
    [
        (_status_exc(AuthenticationError, 401), "llm_auth_failed"),
        (_status_exc(RateLimitError, 429), "llm_rate_limited"),
        (_status_exc(NotFoundError, 404), "llm_model_not_found"),
        (_status_exc(BadRequestError, 400), "llm_bad_request"),
        (APITimeoutError(request=REQ), "llm_unavailable"),
        (APIConnectionError(request=REQ), "llm_unavailable"),
        (RuntimeError(KEY), "llm_unavailable"),
    ],
)
def test_map_llm_error_codes(exc, code):
    err = map_llm_error(exc)
    assert err.code == code and KEY not in err.message and "boom" not in err.message


def test_response_format_detection():
    yes = _status_exc(BadRequestError, 400)
    yes.message = "response_format is not supported"
    assert is_response_format_unsupported(yes)
    assert not is_response_format_unsupported(_status_exc(BadRequestError, 400))
    assert not is_response_format_unsupported(RuntimeError("response_format"))


@pytest.mark.parametrize(
    ("cls", "status", "message"),
    [
        (BadRequestError, 400, "Unsupported parameter: 'response_format'"),
        (BadRequestError, 400, "Invalid parameter: response format is not supported by this model"),
        (BadRequestError, 400, "This model does not support JSON mode"),
        (BadRequestError, 400, "'json_object' is not a valid type for this deployment"),
        (BadRequestError, 400, "Structured outputs are not supported by this model"),
        (UnprocessableEntityError, 422, "Extra inputs are not permitted: response_format"),
        (APIStatusError, 405, "response_format is not allowed on this route"),
        (APIStatusError, 415, "Unrecognized request argument supplied: response_format"),
        (APIStatusError, 501, "response_format not implemented"),
        (NotFoundError, 404, "Unknown field response_format"),
    ],
)
def test_response_format_detection_covers_gateway_wordings(cls, status, message):
    exc = _status_exc(cls, status)
    exc.message = message
    assert is_response_format_unsupported(exc)


@pytest.mark.parametrize(
    ("cls", "status", "message"),
    [
        (BadRequestError, 400, "Invalid API key format"),
        (BadRequestError, 400, "maximum context length exceeded"),
        (NotFoundError, 404, "The model `gpt-9` does not exist"),
        (AuthenticationError, 401, "response_format denied for this key"),
        (RateLimitError, 429, "response_format rate limit"),
        (APIStatusError, 500, "response_format crashed the server"),
    ],
)
def test_response_format_detection_ignores_unrelated_failures(cls, status, message):
    exc = _status_exc(cls, status)
    exc.message = message
    assert not is_response_format_unsupported(exc)


def test_build_chat_model(profile_openai, settings):
    m = build_chat_model(profile_openai, KEY, settings=settings)
    assert isinstance(m, ChatOpenAI) and m.temperature == 0 and m.max_retries == 0
    assert KEY not in repr(m) and KEY not in str(m)
    fake = LlmProfile(name="f", preset="fake", base_url="", model="d", is_default=False)
    assert isinstance(build_chat_model(fake, "", settings=settings), ScriptedChatModel)
    assert json_mode_kwargs() == {"response_format": {"type": "json_object"}}


async def test_a_timeout_is_not_retried(profile_openai, settings):
    calls = []

    def h(req: httpx.Request) -> httpx.Response:
        calls.append(req.url.path)
        raise httpx.ReadTimeout("slow", request=req)

    r = await probe_profile(
        profile_openai, KEY, settings=settings, http_async_client=mock_openai(h)
    )
    assert not r.ok
    assert len(calls) == 1  # no hidden client retry: one call costs at most one timeout
