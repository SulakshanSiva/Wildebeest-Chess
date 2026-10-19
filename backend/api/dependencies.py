from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from ..application.game_service import GameService


def get_game_service(request: Request) -> GameService:
    """
    Hand a route the application's one game service.

    The service is built once in the app factory and kept on the app, so every
    request sees the same games, and a test app gets its own isolated service.

    Arguments:
        request: The incoming request, which knows its app.

    Returns:
        The game service.
    """
    service: GameService = request.app.state.game_service
    return service


GameServiceDep = Annotated[GameService, Depends(get_game_service)]
