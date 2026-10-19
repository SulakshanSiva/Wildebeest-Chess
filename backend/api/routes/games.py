from __future__ import annotations

from fastapi import APIRouter, status

from ..dependencies import GameServiceDep
from ..mappers import game_response, to_color, to_coordinate
from ..schemas.games import CreateGameRequest, GameResponse, SubmitMoveRequest

router = APIRouter(prefix="/games", tags=["games"])


# Routes are plain functions rather than async ones on purpose: FastAPI runs
# them in a worker thread, so an AI search never blocks other requests.
@router.post("", status_code=status.HTTP_201_CREATED)
def create_game(body: CreateGameRequest, service: GameServiceDep) -> GameResponse:
    """
    Start a game against the computer.

    Arguments:
        body: Which colour the person plays.
        service: The game service.

    Returns:
        The new game. If the person plays Black, it includes the AI's first move.
    """
    return game_response(service.create_game(to_color(body.human_color)))


@router.get("/{game_id}")
def get_game(game_id: str, service: GameServiceDep) -> GameResponse:
    """
    Fetch a game as it stands, for example after a page reload.

    Arguments:
        game_id: The game to fetch.
        service: The game service.

    Returns:
        The game, with no turns.
    """
    return game_response(service.get_game(game_id))


@router.post("/{game_id}/moves")
def submit_move(game_id: str, body: SubmitMoveRequest, service: GameServiceDep) -> GameResponse:
    """
    Make the person's move. The computer replies in the same request.

    Arguments:
        game_id: The game to move in.
        body: The move, and the version it was chosen against.
        service: The game service.

    Returns:
        The game after both moves, with both turns.
    """
    view = service.submit_move(
        game_id,
        origin=to_coordinate(body.origin),
        destination=to_coordinate(body.destination),
        expected_version=body.expected_version,
        actor=None if body.actor is None else to_coordinate(body.actor),
    )
    return game_response(view)


@router.post("/{game_id}/resign")
def resign(game_id: str, service: GameServiceDep) -> GameResponse:
    """
    Concede the game to the computer.

    Arguments:
        game_id: The game to resign.
        service: The game service.

    Returns:
        The finished game.
    """
    return game_response(service.resign(game_id))
