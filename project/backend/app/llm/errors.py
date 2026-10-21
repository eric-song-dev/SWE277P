import re

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
)

from app.errors import HubError


def map_llm_error(exc: Exception) -> HubError:
    """Translate a provider failure into a HubError.

    Messages are fixed text: the provider's raw body is never included, because it can echo the key.
    """
    if isinstance(exc, AuthenticationError):
        return HubError(
            "llm_auth_failed",
            "The AI provider rejected the API key. Check this profile in Settings.",
            status_code=502,
        )
    if isinstance(exc, RateLimitError):
        return HubError(
            "llm_rate_limited",
            "The AI provider is rate-limiting requests. Wait a moment and try again.",
            status_code=429,
        )
    if isinstance(exc, APIConnectionError):  # includes APITimeoutError
        return HubError(
            "llm_unavailable",
            "Could not reach the AI provider. Check the base URL and your network, then retry.",
            status_code=502,
        )
    if isinstance(exc, NotFoundError):
        return HubError(
            "llm_model_not_found",
            "The AI provider does not know this model or URL. Check the model name and base URL.",
            status_code=502,
        )
    if isinstance(exc, APIStatusError) and exc.status_code >= 500:
        return HubError(
            "llm_unavailable",
            "The AI provider had an error. Try again in a moment.",
            status_code=502,
        )
    if isinstance(exc, BadRequestError | APIStatusError):
        return HubError(
            "llm_bad_request",
            "The AI provider rejected the request. Check the model and settings of this profile.",
            status_code=400,
        )
    return HubError(
        "llm_unavailable",
        "The AI request failed unexpectedly. Try again.",
        status_code=502,
    )


# Statuses OpenAI-compatible gateways use to refuse a request field they do not support.
_REJECTION_STATUSES = frozenset({400, 404, 405, 415, 422, 501})
# Wordings that name the JSON-mode / structured-output feature (never a key or model problem).
_REJECTION_WORDING = re.compile(
    r"response[_\s-]?format|json[_\s-]?object|json[_\s-]?schema|json[_\s-]?mode|structured[_\s-]?output",
    re.IGNORECASE,
)


def is_response_format_unsupported(exc: Exception) -> bool:
    """True if the provider refused ``response_format``/JSON mode (spec 7.3): the plain-call
    fallback then applies. Needs both a rejection-type status and a message about the feature,
    so auth, rate-limit, server and unrelated 4xx errors are not mistaken for it."""
    return (
        isinstance(exc, APIStatusError)
        and exc.status_code in _REJECTION_STATUSES
        and bool(_REJECTION_WORDING.search(str(exc.message)))
    )
