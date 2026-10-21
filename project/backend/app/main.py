from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.errors import install_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="UCI GPSRC Data Hub")
    install_error_handlers(app)

    app.include_router(auth_router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
