from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.dataset.router import router as dataset_router
from app.errors import install_error_handlers
from app.events.router import router as events_router
from app.imports.router import router as imports_router


def create_app() -> FastAPI:
    app = FastAPI(title="UCI GPSRC Data Hub")
    install_error_handlers(app)

    app.include_router(auth_router)
    app.include_router(imports_router)
    app.include_router(events_router)
    app.include_router(dataset_router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
