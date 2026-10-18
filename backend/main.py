from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.errors import register_error_handlers
from .api.routes import health, variants
from .config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Build the application.

    A factory rather than a module-level app, so tests can build an isolated
    instance with their own settings and startup creates no game state.

    Arguments:
        settings: Configuration to use. Read from the environment when omitted.

    Returns:
        A configured FastAPI application.
    """
    resolved = settings or Settings.from_environment()

    app = FastAPI(
        title="Wildebeest Chess",
        version="0.1.0",
        summary="Authoritative rules engine for an 11x11 chess variant.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    api = APIRouter(prefix=resolved.api_prefix)
    api.include_router(health.router)
    api.include_router(variants.router)
    app.include_router(api)

    register_error_handlers(app)
    return app


app = create_app()
