import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config import Settings
from app.llm.fake import ScriptedChatModel
from app.llm.models import LlmProfile


def build_chat_model(
    profile: LlmProfile,
    api_key: str,
    *,
    settings: Settings,
    http_async_client: httpx.AsyncClient | None = None,
) -> BaseChatModel:
    if profile.preset == "fake":
        return ScriptedChatModel.default()
    return ChatOpenAI(
        base_url=profile.base_url,
        api_key=SecretStr(api_key),
        model=profile.model,
        temperature=0,
        timeout=settings.llm_timeout_s,
        max_retries=1,
        http_async_client=http_async_client,
    )


def json_mode_kwargs() -> dict:
    return {"response_format": {"type": "json_object"}}
