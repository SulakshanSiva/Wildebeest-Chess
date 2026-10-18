from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.domain.enums import PieceKind, Terrain
from backend.domain.errors import (
    AmbiguousMoveError,
    DomainError,
    GameOverError,
    IllegalMoveError,
    InvariantViolation,
    OutOfBoundsError,
    StaleVersionError,
)
from backend.main import create_app

PREFIX = "/api/v1"
VARIANT_URL = f"{PREFIX}/variants/wildebeest"


@pytest.fixture
def app() -> FastAPI:
    """
    Build an isolated application with default settings.

    Returns:
        A fresh application, so no test shares state with another.
    """
    return create_app(Settings())


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """
    Give an HTTP client bound to the test application.

    Arguments:
        app: The application under test.

    Returns:
        A client that does not raise on server errors, so status codes can be
        asserted.
    """
    return TestClient(app, raise_server_exceptions=False)


def test_health_reports_ok(client: TestClient) -> None:
    """
    Answer the liveness check without depending on any game.

    Arguments:
        client: Client for the test application.
    """
    response = client.get(f"{PREFIX}/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_the_variant_describes_the_board(client: TestClient) -> None:
    """
    Serve dimensions and first player for the shipped variant.

    Arguments:
        client: Client for the test application.
    """
    body = client.get(VARIANT_URL).json()

    assert (body["rows"], body["columns"]) == (11, 11)
    assert body["first_player"] == "white"
    assert body["variant_id"] == "wildebeest"


def test_the_variant_lists_every_piece_and_terrain(client: TestClient) -> None:
    """
    Cover every piece kind and terrain, each with a symbol and description.

    Arguments:
        client: Client for the test application.
    """
    body = client.get(VARIANT_URL).json()

    assert {entry["kind"] for entry in body["pieces"]} == {kind.value for kind in PieceKind}
    assert all(entry["movement"] for entry in body["pieces"])
    assert {entry["symbol"] for entry in body["terrain"]} == {t.symbol for t in Terrain}


def test_an_unknown_variant_is_not_found(client: TestClient) -> None:
    """
    Return 404 rather than silently serving the default variant.

    Arguments:
        client: Client for the test application.
    """
    assert client.get(f"{PREFIX}/variants/unknown").status_code == 404


def test_a_domain_error_becomes_a_client_error(app: FastAPI, client: TestClient) -> None:
    """
    Map an expected domain error onto its documented status and a stable body.

    Arguments:
        app: The application under test.
        client: Client for the test application.
    """

    @app.get("/raise-domain-error")
    def _raise() -> None:
        """
        Fail with an expected domain error.
        """
        raise OutOfBoundsError(12, 3, 11, 11)

    response = client.get("/raise-domain-error")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "OutOfBoundsError"
    assert "outside" in response.json()["error"]["message"]


def test_an_invariant_violation_hides_its_detail(app: FastAPI, client: TestClient) -> None:
    """
    Report an engine defect as a 500 without leaking its message.

    This also pins the handler order: InvariantViolation subclasses DomainError,
    so if the general handler won, this would come back as a 400.

    Arguments:
        app: The application under test.
        client: Client for the test application.
    """

    @app.get("/raise-invariant")
    def _raise() -> None:
        """
        Fail with an engine defect.
        """
        raise InvariantViolation("piece id 7 appears twice")

    response = client.get("/raise-invariant")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "InvariantViolation"
    assert "piece id 7" not in response.text


@pytest.mark.parametrize(
    "error,status",
    [
        (IllegalMoveError("no legal move"), 422),
        (AmbiguousMoveError("two moves match"), 422),
        (GameOverError(), 409),
        (StaleVersionError(expected=3, actual=4), 409),
    ],
    ids=["illegal", "ambiguous", "game-over", "stale-version"],
)
def test_game_errors_map_to_their_documented_status(
    app: FastAPI, client: TestClient, error: DomainError, status: int
) -> None:
    """
    Map each game error onto its status, so the routes inherit the policy.

    A stale version and a finished game are conflicts with the game's state, not
    malformed input, so they must not fall back to the default 400.

    Arguments:
        app: The application under test.
        client: Client for the test application.
        error: The error the route raises.
        status: The status the client should see.
    """

    @app.get("/raise-game-error")
    def _raise() -> None:
        """
        Fail with the parametrised game error.
        """
        raise error

    response = client.get("/raise-game-error")

    assert response.status_code == status
    assert response.json()["error"]["code"] == type(error).__name__
