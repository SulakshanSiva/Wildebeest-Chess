from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ai.minimax import MinimaxPlayer
from .api.errors import register_error_handlers
from .api.routes import games, health, variants
from .application.game_service import GameService
from .application.game_store import InMemoryGameStore
from .config import Settings
from .domain.variant import Variant


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Build the application.

    A factory rather than a module-level app, so each test can build an isolated
    instance with its own settings and its own empty game store.

    Arguments:
        settings: Configuration to use. Read from the environment when omitted.

    Returns:
        A configured FastAPI application.
    """
    resolved = settings or Settings.from_environment()

    app = FastAPI(
        title="Wildebeest Chess",
        version="0.1.0",
        summary="Play an 11x11 chess variant against a computer opponent.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    # One service for the whole process: games live in its store, in memory.
    app.state.game_service = GameService(
        store=InMemoryGameStore(
            ttl_seconds=resolved.game_ttl_seconds,
            max_games=resolved.max_games,
        ),
        ai=MinimaxPlayer(depth=resolved.ai_depth),
        variant=Variant(),
    )

    api = APIRouter(prefix=resolved.api_prefix)
    api.include_router(health.router)
    api.include_router(variants.router)
    api.include_router(games.router)
    app.include_router(api)

    register_error_handlers(app)
    return app


app = create_app()
