from __future__ import annotations

import random

import pytest

from backend.domain.board import Board, BoardDimensions
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, EndReason, GameStatus, PieceKind
from backend.domain.errors import (
    GameOverError,
    IllegalMoveError,
    StaleVersionError,
)
from backend.domain.game import Game
from backend.domain.pieces.registry import create_piece
from backend.domain.position import Position
from backend.domain.variant import Variant

KNIGHT_FROM = Coordinate(0, 1)
KNIGHT_TO = Coordinate(2, 2)
PLAYOUT_SEEDS = range(12)
PLAYOUT_LIMIT = 250


@pytest.fixture
def game() -> Game:
    """
    Give a fresh game of the shipped variant.

    Returns:
        A game at version zero with White to move.
    """
    return Game.start("game-1", Variant())


def _two_kings_game(extra: list[tuple[Coordinate, PieceKind, Color]]) -> Game:
    """
    Build a small game with a King each plus any extra pieces.

    Arguments:
        extra: Further pieces to place, as square, kind and colour.

    Returns:
        A game on an 11x11 board holding those pieces.
    """
    return _custom_game(
        [
            (Coordinate(0, 0), PieceKind.KING, Color.WHITE),
            (Coordinate(10, 10), PieceKind.KING, Color.BLACK),
            *extra,
        ]
    )


def test_a_new_game_starts_active_with_white_to_move(game: Game) -> None:
    """
    Begin at version zero, active, with no history.

    Arguments:
        game: A fresh game.
    """
    assert game.status is GameStatus.ACTIVE
    assert game.side_to_move is Color.WHITE
    assert game.version == 0
    assert game.history == ()
    assert game.end_reason is None


def test_a_legal_move_hands_over_the_turn_and_bumps_the_version(game: Game) -> None:
    """
    Advance one turn: new side to move, version up, one record kept.

    Arguments:
        game: A fresh game.
    """
    move = game.find_move(KNIGHT_FROM, KNIGHT_TO)

    after = game.apply_move(move)

    assert after.side_to_move is Color.BLACK
    assert after.version == 1
    assert len(after.history) == 1
    assert after.history[0].side is Color.WHITE
    assert after.history[0].ply == 0


def test_applying_a_move_leaves_the_original_game_untouched(game: Game) -> None:
    """
    Keep a game immutable, so a reader is never disturbed by a writer.

    Arguments:
        game: A fresh game.
    """
    before_board = str(game.position.board)

    game.apply_move(game.find_move(KNIGHT_FROM, KNIGHT_TO))

    assert str(game.position.board) == before_board
    assert game.version == 0


def test_an_illegal_move_is_refused(game: Game) -> None:
    """
    Reject squares that name no legal move.

    Arguments:
        game: A fresh game.
    """
    with pytest.raises(IllegalMoveError):
        game.find_move(Coordinate(0, 0), Coordinate(5, 5))


def test_a_move_for_the_wrong_side_is_refused(game: Game) -> None:
    """
    Refuse Black's piece while it is White's turn.

    Arguments:
        game: A fresh game.
    """
    with pytest.raises(IllegalMoveError):
        game.find_move(Coordinate(10, 1), Coordinate(8, 2))


def test_a_stale_version_is_refused(game: Game) -> None:
    """
    Reject a command built against an older version of the game.

    Arguments:
        game: A fresh game.
    """
    move = game.find_move(KNIGHT_FROM, KNIGHT_TO)

    with pytest.raises(StaleVersionError) as raised:
        game.apply_move(move, expected_version=3)

    assert raised.value.expected == 3
    assert raised.value.actual == 0


def test_the_matching_version_is_accepted(game: Game) -> None:
    """
    Accept a command whose expected version is current.

    Arguments:
        game: A fresh game.
    """
    move = game.find_move(KNIGHT_FROM, KNIGHT_TO)

    assert game.apply_move(move, expected_version=0).version == 1


def test_a_move_that_is_not_in_the_legal_list_is_refused(game: Game) -> None:
    """
    Reject a hand-built Move that no piece could produce.

    Arguments:
        game: A fresh game.
    """
    legal = game.find_move(KNIGHT_FROM, KNIGHT_TO)
    forged = type(legal)(
        actor=legal.actor,
        origin=legal.origin,
        destination=Coordinate(9, 9),
        action=legal.action,
    )

    with pytest.raises(IllegalMoveError):
        game.apply_move(forged)


def test_capturing_the_king_ends_the_game() -> None:
    """
    Award the win to the side that takes the opposing King.
    """
    white = _two_kings_game([(Coordinate(10, 5), PieceKind.ROOK, Color.WHITE)])

    won = white.apply_move(white.find_move(Coordinate(10, 5), Coordinate(10, 10)))

    assert won.status is GameStatus.WHITE_WINS
    assert won.end_reason is EndReason.KING_CAPTURED
    assert won.history[0].captured[0][1] is PieceKind.KING


def test_a_finished_game_accepts_no_more_moves() -> None:
    """
    Refuse every command once the game has been decided.
    """
    white = _two_kings_game([(Coordinate(10, 5), PieceKind.ROOK, Color.WHITE)])
    won = white.apply_move(white.find_move(Coordinate(10, 5), Coordinate(10, 10)))

    assert won.legal_moves() == ()
    with pytest.raises(GameOverError):
        won.apply_move(white.legal_moves()[0])
    with pytest.raises(GameOverError):
        won.resign(Color.BLACK)


@pytest.mark.parametrize(
    "side,expected",
    [(Color.WHITE, GameStatus.BLACK_WINS), (Color.BLACK, GameStatus.WHITE_WINS)],
    ids=["white-resigns", "black-resigns"],
)
def test_resigning_hands_the_win_to_the_opponent(
    game: Game, side: Color, expected: GameStatus
) -> None:
    """
    End the game in the opponent's favour.

    Arguments:
        game: A fresh game.
        side: The colour that resigns.
        expected: The status that should follow.
    """
    ended = game.resign(side)

    assert ended.status is expected
    assert ended.end_reason is EndReason.RESIGNATION
    assert ended.version == 1


def test_resigning_checks_the_version(game: Game) -> None:
    """
    Reject a resignation built against an older version.

    Arguments:
        game: A fresh game.
    """
    with pytest.raises(StaleVersionError):
        game.resign(Color.WHITE, expected_version=9)


def _custom_game(pieces: list[tuple[Coordinate, PieceKind, Color]]) -> Game:
    """
    Build a game from exactly the given pieces, White to move.

    Arguments:
        pieces: Every piece on the board, as square, kind and colour.

    Returns:
        A game on an 11x11 board holding only those pieces.
    """
    board = Board.empty(BoardDimensions(11, 11))
    for index, (square, kind, colour) in enumerate(pieces, start=1):
        board = board.with_piece(square, create_piece(index, kind, colour))
    return Game(
        game_id="custom",
        variant=Variant(),
        position=Position(board=board, side_to_move=Color.WHITE),
    )


def test_losing_both_kings_in_one_turn_is_a_draw() -> None:
    """
    Call it a draw when one explosion takes both Kings together.

    Joey's row holds five pieces after the move (the Kings stand one row up),
    so he detonates, and both Kings are among his neighbours.
    """
    game = _custom_game(
        [
            (Coordinate(5, 4), PieceKind.JOEY, Color.WHITE),
            (Coordinate(4, 4), PieceKind.KING, Color.WHITE),
            (Coordinate(4, 5), PieceKind.KING, Color.BLACK),
            (Coordinate(5, 0), PieceKind.ROOK, Color.WHITE),
            (Coordinate(5, 5), PieceKind.PAWN, Color.BLACK),
            (Coordinate(5, 8), PieceKind.PAWN, Color.BLACK),
            (Coordinate(5, 10), PieceKind.PAWN, Color.BLACK),
        ]
    )

    after = game.apply_move(game.find_move(Coordinate(5, 0), Coordinate(5, 1)))

    assert after.status is GameStatus.DRAW
    assert after.end_reason is EndReason.KING_CAPTURED


def test_a_side_with_no_legal_moves_ends_the_game_as_a_draw() -> None:
    """
    Draw rather than hang when the side to move has nothing it may do.

    The rules never address this, so it is an assumption recorded in the
    architecture document. Black's only piece is a King held by a BeeKeeper.
    """
    game = _custom_game(
        [
            (Coordinate(0, 0), PieceKind.KING, Color.WHITE),
            (Coordinate(9, 9), PieceKind.BEEKEEPER, Color.WHITE),
            (Coordinate(10, 10), PieceKind.KING, Color.BLACK),
        ]
    )

    after = game.apply_move(game.find_move(Coordinate(0, 0), Coordinate(0, 1)))

    assert after.status is GameStatus.DRAW
    assert after.end_reason is EndReason.NO_LEGAL_MOVES


def test_naming_the_wrong_actor_finds_no_move(game: Game) -> None:
    """
    Use the actor to narrow a match, and refuse when it matches nothing.

    Arguments:
        game: A fresh game.
    """
    with pytest.raises(IllegalMoveError):
        game.find_move(KNIGHT_FROM, KNIGHT_TO, actor=Coordinate(0, 0))


@pytest.mark.parametrize("seed", PLAYOUT_SEEDS)
def test_random_games_keep_every_invariant(seed: int) -> None:
    """
    Play random legal moves and check the engine's own promises each turn.

    A property-style test: whatever sequence of legal moves is chosen, the board
    stays well formed, piece ids stay unique, history stays in step with the
    version, and a decided game stays decided.

    Arguments:
        seed: Seed for the random choice of moves, for reproducibility.
    """
    rng = random.Random(seed)
    game = Game.start(f"playout-{seed}", Variant())

    for _ in range(PLAYOUT_LIMIT):
        moves = game.legal_moves()
        if not moves:
            break
        game = game.apply_move(rng.choice(moves))

        game.position.board.validate()
        assert game.version == len(game.history)
        assert game.history[-1].ply == len(game.history) - 1
        if game.status.is_over:
            assert game.end_reason is not None
            assert game.legal_moves() == ()
            break
