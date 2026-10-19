from __future__ import annotations

import threading
from itertools import count

import pytest

from backend.ai.minimax import MinimaxPlayer
from backend.application.errors import GameNotFoundError
from backend.application.game_service import GameService
from backend.application.game_store import InMemoryGameStore
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, EndReason, GameStatus
from backend.domain.errors import GameOverError, IllegalMoveError, StaleVersionError
from backend.domain.variant import Variant

KNIGHT_FROM = Coordinate(0, 1)
KNIGHT_TO = Coordinate(2, 2)

# White's rook can take Black's King at once, so the game ends on White's move.
KING_HUNT_LAYOUT = """
K...
....
.R.k
"""


def _service(variant: Variant | None = None) -> GameService:
    """
    Build a service with a fast AI and predictable game ids.

    Arguments:
        variant: The ruleset to play, the shipped one by default.

    Returns:
        A service whose games are named game-1, game-2 and so on.
    """
    ids = count(1)
    return GameService(
        store=InMemoryGameStore(ttl_seconds=3600, max_games=10),
        ai=MinimaxPlayer(depth=1),
        variant=variant or Variant(),
        new_game_id=lambda: f"game-{next(ids)}",
    )


@pytest.fixture
def service() -> GameService:
    """
    Give a fresh service for the shipped variant.

    Returns:
        A service with no games yet.
    """
    return _service()


def test_playing_white_waits_for_the_persons_first_move(service: GameService) -> None:
    """
    Hand back an untouched game when the person moves first.

    Arguments:
        service: A fresh service.
    """
    view = service.create_game(Color.WHITE)

    assert view.session.game.version == 0
    assert view.session.game.side_to_move is Color.WHITE
    assert view.turns == ()


def test_playing_black_lets_the_ai_open(service: GameService) -> None:
    """
    Play the AI's opening move first when the person takes Black.

    Arguments:
        service: A fresh service.
    """
    view = service.create_game(Color.BLACK)

    assert view.session.game.version == 1
    assert view.session.game.side_to_move is Color.BLACK
    assert [turn.side for turn in view.turns] == [Color.WHITE]


def test_a_created_game_can_be_looked_up(service: GameService) -> None:
    """
    Store a new game so later requests find it.

    Arguments:
        service: A fresh service.
    """
    created = service.create_game(Color.WHITE)

    looked_up = service.get_game(created.session.game_id)

    assert looked_up.session.game.version == 0
    assert looked_up.turns == ()


def test_a_move_is_answered_by_the_ai(service: GameService) -> None:
    """
    Apply the person's move and the AI's reply in one request.

    Arguments:
        service: A fresh service.
    """
    game_id = service.create_game(Color.WHITE).session.game_id

    view = service.submit_move(game_id, KNIGHT_FROM, KNIGHT_TO, expected_version=0)

    assert view.session.game.version == 2
    assert [turn.side for turn in view.turns] == [Color.WHITE, Color.BLACK]
    assert view.session.game.side_to_move is Color.WHITE


def test_a_move_is_kept_for_the_next_request(service: GameService) -> None:
    """
    Store the game after a move, so the next lookup sees it.

    Arguments:
        service: A fresh service.
    """
    game_id = service.create_game(Color.WHITE).session.game_id
    service.submit_move(game_id, KNIGHT_FROM, KNIGHT_TO, expected_version=0)

    assert service.get_game(game_id).session.game.version == 2


def test_a_stale_move_is_refused(service: GameService) -> None:
    """
    Refuse a move chosen against an older version of the game.

    Arguments:
        service: A fresh service.
    """
    game_id = service.create_game(Color.WHITE).session.game_id
    service.submit_move(game_id, KNIGHT_FROM, KNIGHT_TO, expected_version=0)

    with pytest.raises(StaleVersionError):
        service.submit_move(game_id, Coordinate(0, 9), Coordinate(2, 8), expected_version=0)


def test_staleness_is_reported_before_illegality(service: GameService) -> None:
    """
    Report an out-of-date move as stale even if it is also illegal now.

    The caller needs to know to reload; being told the move is illegal would
    send them looking for a mistake they did not make.

    Arguments:
        service: A fresh service.
    """
    game_id = service.create_game(Color.WHITE).session.game_id
    service.submit_move(game_id, KNIGHT_FROM, KNIGHT_TO, expected_version=0)

    with pytest.raises(StaleVersionError):
        service.submit_move(game_id, KNIGHT_FROM, KNIGHT_TO, expected_version=0)


def test_an_illegal_move_changes_nothing(service: GameService) -> None:
    """
    Refuse an illegal move and leave the stored game as it was.

    Arguments:
        service: A fresh service.
    """
    game_id = service.create_game(Color.WHITE).session.game_id

    with pytest.raises(IllegalMoveError):
        service.submit_move(game_id, Coordinate(0, 0), Coordinate(5, 5), expected_version=0)
    assert service.get_game(game_id).session.game.version == 0


def test_an_unknown_game_is_not_found(service: GameService) -> None:
    """
    Raise a named error for a game id that does not exist.

    Arguments:
        service: A fresh service.
    """
    with pytest.raises(GameNotFoundError):
        service.get_game("nope")
    with pytest.raises(GameNotFoundError):
        service.submit_move("nope", KNIGHT_FROM, KNIGHT_TO, expected_version=0)


def test_a_winning_move_gets_no_ai_reply() -> None:
    """
    Stop once the person wins, without asking the AI to move in a finished game.
    """
    service = _service(Variant(layout=KING_HUNT_LAYOUT, transporter_links={}))
    game_id = service.create_game(Color.WHITE).session.game_id

    view = service.submit_move(game_id, Coordinate(2, 1), Coordinate(2, 3), expected_version=0)

    assert view.session.game.status is GameStatus.WHITE_WINS
    assert [turn.side for turn in view.turns] == [Color.WHITE]
    with pytest.raises(GameOverError):
        service.submit_move(game_id, Coordinate(0, 0), Coordinate(0, 1), expected_version=1)


def test_two_moves_sent_at_once_cannot_both_be_applied(service: GameService) -> None:
    """
    Accept exactly one of two moves sent at the same time against one version.

    This is the double-click and two-tabs case. The per-game lock makes the
    moves run one after the other, so the second sees the newer version and is
    refused as stale rather than applied on top of a position it never saw.

    Arguments:
        service: A fresh service.
    """
    game_id = service.create_game(Color.WHITE).session.game_id
    outcomes: list[str] = []
    gate = threading.Barrier(2)

    def send() -> None:
        """
        Wait for the other request, then submit the same move.
        """
        gate.wait()
        try:
            service.submit_move(game_id, KNIGHT_FROM, KNIGHT_TO, expected_version=0)
            outcomes.append("applied")
        except StaleVersionError:
            outcomes.append("stale")

    threads = [threading.Thread(target=send) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["applied", "stale"]
    assert service.get_game(game_id).session.game.version == 2


@pytest.mark.parametrize(
    "human,winner",
    [(Color.WHITE, GameStatus.BLACK_WINS), (Color.BLACK, GameStatus.WHITE_WINS)],
    ids=["white-resigns", "black-resigns"],
)
def test_resigning_hands_the_win_to_the_ai(
    service: GameService, human: Color, winner: GameStatus
) -> None:
    """
    End the game in the computer's favour, whichever colour the person plays.

    Arguments:
        service: A fresh service.
        human: The colour the person plays.
        winner: The status that should follow.
    """
    created = service.create_game(human)

    view = service.resign(created.session.game_id)

    assert view.session.game.status is winner
    assert view.session.game.end_reason is EndReason.RESIGNATION
    assert view.session.game.version == created.session.game.version + 1
    assert view.turns == ()


def test_a_resignation_is_kept(service: GameService) -> None:
    """
    Store the resigned game, so a later lookup shows it finished.

    Arguments:
        service: A fresh service.
    """
    game_id = service.create_game(Color.WHITE).session.game_id
    service.resign(game_id)

    assert service.get_game(game_id).session.game.status is GameStatus.BLACK_WINS


def test_a_finished_game_cannot_be_resigned_or_moved_in(service: GameService) -> None:
    """
    Refuse every further action once the person has resigned.

    Arguments:
        service: A fresh service.
    """
    game_id = service.create_game(Color.WHITE).session.game_id
    service.resign(game_id)

    with pytest.raises(GameOverError):
        service.resign(game_id)
    with pytest.raises(GameOverError):
        service.submit_move(game_id, KNIGHT_FROM, KNIGHT_TO, expected_version=1)


def test_resigning_an_unknown_game_is_not_found(service: GameService) -> None:
    """
    Raise a named error when resigning a game that does not exist.

    Arguments:
        service: A fresh service.
    """
    with pytest.raises(GameNotFoundError):
        service.resign("nope")
