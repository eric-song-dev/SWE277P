import time

import httpx

from app.config import Settings
from app.llm.errors import is_response_format_unsupported, map_llm_error
from app.llm.factory import build_chat_model, json_mode_kwargs
from app.llm.models import LlmProfile
from app.llm.schemas import ProbeResultOut

PROBE_PROMPT = 'Reply with {"ok": true}'


def _ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


async def _list_models(
    profile: LlmProfile,
    api_key: str,
    settings: Settings,
    http_async_client: httpx.AsyncClient | None,
) -> list[str]:
    """Best effort: any failure just means no suggestions."""
    client = http_async_client or httpx.AsyncClient(timeout=settings.llm_timeout_s)
    try:
        res = await client.get(
            f"{profile.base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        res.raise_for_status()
        return sorted({str(m["id"]) for m in res.json()["data"] if m.get("id")})
    except Exception:  # noqa: BLE001
        return []
    finally:
        if http_async_client is None:
            await client.aclose()


async def probe_profile(
    profile: LlmProfile,
    api_key: str,
    *,
    settings: Settings,
    http_async_client: httpx.AsyncClient | None = None,
) -> ProbeResultOut:
    start = time.monotonic()
    if profile.preset == "fake":
        return ProbeResultOut(ok=True, json_mode=True, models=[], latency_ms=_ms(start))
    model = build_chat_model(
        profile, api_key, settings=settings, http_async_client=http_async_client
    )
    json_mode: bool | None = True
    try:
        try:
            await model.bind(**json_mode_kwargs()).ainvoke(PROBE_PROMPT)
        except Exception as exc:
            if not is_response_format_unsupported(exc):
                raise
            json_mode = False
            await model.ainvoke(PROBE_PROMPT)
    except Exception as exc:  # noqa: BLE001
        err = map_llm_error(exc)
        return ProbeResultOut(ok=False, error=err.message, latency_ms=_ms(start))
    latency = _ms(start)
    models = await _list_models(profile, api_key, settings, http_async_client)
    return ProbeResultOut(ok=True, json_mode=json_mode, models=models, latency_ms=latency)
