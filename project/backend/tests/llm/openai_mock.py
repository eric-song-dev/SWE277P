import json
from collections.abc import Callable

import httpx

Handler = Callable[[httpx.Request], httpx.Response]


def chat_reply(content: str) -> httpx.Response:
    body = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    return httpx.Response(200, json=body)


def models_reply(*ids: str) -> httpx.Response:
    return httpx.Response(
        200, json={"object": "list", "data": [{"id": i, "object": "model"} for i in ids]}
    )


def error_reply(status: int, message: str) -> httpx.Response:
    return httpx.Response(status, json={"error": {"message": message, "type": "error"}})


def request_json(request: httpx.Request) -> dict:
    return json.loads(request.content or b"{}")


def mock_openai(handler: Handler) -> httpx.AsyncClient:
    """An AsyncClient whose transport calls `handler(request)`; no network."""
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))
