import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

# Validation errors are returned without `input` (the submitted value, e.g. an API key), `ctx`
# or `url`.
_VALIDATION_ERROR_KEYS = ("loc", "msg", "type")


class HubError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def error_response(
    status_code: int, code: str, message: str, details: object | None = None
) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "details": details}}
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body))


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HubError)
    async def _hub_error(request: Request, exc: HubError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else f"http_{exc.status_code}"
        return error_response(exc.status_code, code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [{k: e[k] for k in _VALIDATION_ERROR_KEYS if k in e} for e in exc.errors()]
        return error_response(422, "validation_error", "Request validation failed", details)

    # Not an `Exception` handler: FastAPI would put that on ServerErrorMiddleware, which re-raises
    # after replying, and uvicorn then logs the full traceback (message and frames included).
    # This middleware sits just inside it, so nothing unhandled ever escapes.
    app.add_middleware(_UnhandledErrorMiddleware)


class _UnhandledErrorMiddleware:
    """Turns any unhandled exception into the generic 500, logging the exception type only."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def tracking_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, tracking_send)
        except Exception as exc:  # noqa: BLE001 - last line of defence
            # Type only, no traceback: the message and frames can carry row values or a key.
            logger.error(
                "Unhandled %s on %s %s", type(exc).__name__, scope["method"], scope["path"]
            )
            if not started:
                response = error_response(500, "internal_error", "Internal server error")
                await response(scope, receive, send)
