import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.config import get_settings
from app.dataset.router import router as dataset_router
from app.db import SessionLocal, get_app_engine
from app.errors import install_error_handlers
from app.events.router import router as events_router
from app.imports.router import router as imports_router
from app.llm.router import router as llm_router
from app.llm.service import seed_profile_from_env

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        with SessionLocal(bind=get_app_engine()) as session:
            seed_profile_from_env(session, get_settings())
            session.commit()
    except Exception as exc:  # noqa: BLE001 - a bad seed must not stop startup
        # Never log the exception text: validation errors can echo the submitted key.
        logger.warning("LLM profile seed skipped (%s)", type(exc).__name__)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="UCI GPSRC Data Hub", lifespan=lifespan)
    install_error_handlers(app)

    app.include_router(auth_router)
    app.include_router(imports_router)
    app.include_router(events_router)
    app.include_router(dataset_router)
    app.include_router(llm_router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
