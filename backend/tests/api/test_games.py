from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app

GAMES = "/api/v1/games"
KNIGHT_MOVE = {"origin": {"row": 0, "column": 1}, "destination": {"row": 2, "column": 2}}


@pytest.fixture
def client() -> TestClient:
    """
    Give a client for an app with its own empty game store and a fast AI.

    Returns:
        A client that does not raise on server errors, so status codes can be
        asserted.
    """
    return TestClient(create_app(Settings(ai_depth=1)), raise_server_exceptions=False)


def _new_game(client: TestClient, colour: str = "white") -> dict[str, Any]:
    """
    Start a game through the API.

    Arguments:
        client: Client for the test application.
        colour: The colour the person plays.

    Returns:
        The response body.
    """
    response = client.post(GAMES, json={"human_color": colour})
    assert response.status_code == 201
    body: dict[str, Any] = response.json()
    return body


def test_starting_a_game_returns_the_opening_position(client: TestClient) -> None:
    """
    Create a game at version zero with the full board and the person's moves.

    Arguments:
        client: Client for the test application.
    """
    game = _new_game(client)

    assert game["version"] == 0
    assert game["status"] == "active"
    assert game["side_to_move"] == "white"
    assert game["human_color"] == "white"
    assert (len(game["board"]), len(game["board"][0])) == (11, 11)
    assert game["board"][0][0]["piece"]["kind"] == "rook"
    assert game["board"][5][5]["terrain"] == "jet_pack"
    assert len(game["legal_moves"]) == 30
    assert game["turns"] == []


def test_starting_as_black_includes_the_ais_opening(client: TestClient) -> None:
    """
    Play the computer's first move before handing the game to a Black player.

    Arguments:
        client: Client for the test application.
    """
    game = _new_game(client, "black")

    assert game["version"] == 1
    assert game["side_to_move"] == "black"
    assert [turn["side"] for turn in game["turns"]] == ["white"]
    assert game["legal_moves"]


def test_making_a_move_returns_both_turns(client: TestClient) -> None:
    """
    Answer the person's move with the computer's in the same response.

    Arguments:
        client: Client for the test application.
    """
    game = _new_game(client)

    response = client.post(
        f"{GAMES}/{game['game_id']}/moves", json={**KNIGHT_MOVE, "expected_version": 0}
    )

    body = response.json()
    assert response.status_code == 200
    assert body["version"] == 2
    assert [turn["side"] for turn in body["turns"]] == ["white", "black"]
    assert body["turns"][0]["move"]["action"] == "move"
    assert body["board"][2][2]["piece"]["kind"] == "knight"


def test_a_game_can_be_fetched_after_a_move(client: TestClient) -> None:
    """
    Return the stored game, as a reloaded page would need.

    Arguments:
        client: Client for the test application.
    """
    game = _new_game(client)
    client.post(f"{GAMES}/{game['game_id']}/moves", json={**KNIGHT_MOVE, "expected_version": 0})

    response = client.get(f"{GAMES}/{game['game_id']}")

    assert response.status_code == 200
    assert response.json()["version"] == 2
    assert response.json()["turns"] == []


def test_an_unknown_game_is_404(client: TestClient) -> None:
    """
    Report a missing game with a 404 and the shared error envelope.

    Arguments:
        client: Client for the test application.
    """
    response = client.get(f"{GAMES}/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "GameNotFoundError"


def test_an_out_of_date_move_is_409(client: TestClient) -> None:
    """
    Report a move sent against an older version as a conflict.

    Arguments:
        client: Client for the test application.
    """
    game = _new_game(client)
    url = f"{GAMES}/{game['game_id']}/moves"
    client.post(url, json={**KNIGHT_MOVE, "expected_version": 0})

    response = client.post(url, json={**KNIGHT_MOVE, "expected_version": 0})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "StaleVersionError"


def test_an_illegal_move_is_422(client: TestClient) -> None:
    """
    Report a move the rules forbid, and leave the game unchanged.

    Arguments:
        client: Client for the test application.
    """
    game = _new_game(client)
    url = f"{GAMES}/{game['game_id']}/moves"
    illegal = {
        "origin": {"row": 0, "column": 0},
        "destination": {"row": 5, "column": 5},
        "expected_version": 0,
    }

    response = client.post(url, json=illegal)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "IllegalMoveError"
    assert client.get(f"{GAMES}/{game['game_id']}").json()["version"] == 0


@pytest.mark.parametrize(
    "body",
    [
        {"origin": {"row": -1, "column": 0}, "destination": {"row": 2, "column": 2}},
        {**KNIGHT_MOVE},
        {**KNIGHT_MOVE, "expected_version": 0, "promote": "queen"},
    ],
    ids=["negative-square", "missing-version", "unknown-field"],
)
def test_a_malformed_move_is_422_in_the_shared_envelope(
    client: TestClient, body: dict[str, Any]
) -> None:
    """
    Reject bodies that do not describe a move, in the same shape as other errors.

    Arguments:
        client: Client for the test application.
        body: The malformed request body.
    """
    game = _new_game(client)

    response = client.post(f"{GAMES}/{game['game_id']}/moves", json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "RequestValidationError"


def test_an_unknown_colour_is_rejected(client: TestClient) -> None:
    """
    Accept only white or black as the person's colour.

    Arguments:
        client: Client for the test application.
    """
    response = client.post(GAMES, json={"human_color": "purple"})

    assert response.status_code == 422


def test_each_app_has_its_own_games() -> None:
    """
    Keep games separate between app instances, so tests cannot leak into each other.
    """
    first = TestClient(create_app(Settings(ai_depth=1)))
    second = TestClient(create_app(Settings(ai_depth=1)))
    game_id = first.post(GAMES, json={"human_color": "white"}).json()["game_id"]

    assert second.get(f"{GAMES}/{game_id}").status_code == 404


def test_resigning_ends_the_game_for_the_computer(client: TestClient) -> None:
    """
    Finish the game in the computer's favour and stop offering moves.

    Arguments:
        client: Client for the test application.
    """
    game = _new_game(client)

    response = client.post(f"{GAMES}/{game['game_id']}/resign")

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "black_wins"
    assert body["end_reason"] == "resignation"
    assert body["legal_moves"] == []
    assert body["turns"] == []


def test_resigning_twice_is_409(client: TestClient) -> None:
    """
    Report a second resignation as a conflict with the finished game.

    Arguments:
        client: Client for the test application.
    """
    game = _new_game(client)
    url = f"{GAMES}/{game['game_id']}/resign"
    client.post(url)

    response = client.post(url)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "GameOverError"


def test_resigning_an_unknown_game_is_404(client: TestClient) -> None:
    """
    Report a resignation for a missing game with a 404.

    Arguments:
        client: Client for the test application.
    """
    assert client.post(f"{GAMES}/does-not-exist/resign").status_code == 404
