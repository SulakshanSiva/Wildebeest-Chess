from __future__ import annotations

import pytest

from backend.ai.evaluation import PROXIMITY_WEIGHT, WIN_SCORE, evaluate, terminal_score
from backend.ai.piece_values import value_of
from backend.domain.board import Board, BoardDimensions
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, GameStatus, PieceKind
from backend.domain.pieces.registry import create_piece
from backend.domain.variant import Variant

BLACK_ROOK = Coordinate(10, 0)


def test_the_opening_position_is_level() -> None:
    """
    Score the symmetric starting position as even for both sides.
    """
    board = Variant().build_board()

    assert evaluate(board, Color.WHITE) == pytest.approx(0)
    assert evaluate(board, Color.BLACK) == pytest.approx(0)


def test_losing_a_piece_moves_the_score_by_its_value() -> None:
    """
    Credit White and debit Black by exactly a rook when Black loses one.

    This corner rook is as far from White's King as the board allows, so it
    carries no proximity bonus and its loss is pure material.
    """
    board = Variant().build_board().without_piece(BLACK_ROOK)
    rook = value_of(PieceKind.ROOK)

    assert evaluate(board, Color.WHITE) == rook
    assert evaluate(board, Color.BLACK) == -rook


@pytest.mark.parametrize(
    "status,perspective,expected_sign",
    [
        (GameStatus.WHITE_WINS, Color.WHITE, 1),
        (GameStatus.WHITE_WINS, Color.BLACK, -1),
        (GameStatus.BLACK_WINS, Color.BLACK, 1),
        (GameStatus.DRAW, Color.WHITE, 0),
    ],
    ids=["white-wins-for-white", "white-wins-for-black", "black-wins-for-black", "draw"],
)
def test_a_finished_game_scores_as_a_win_loss_or_draw(
    status: GameStatus, perspective: Color, expected_sign: int
) -> None:
    """
    Score a decided game far beyond any material total, with the right sign.

    Arguments:
        status: How the game ended.
        perspective: The side the score is for.
        expected_sign: Whether that side won, lost or drew.
    """
    score = terminal_score(status, perspective, ply=1)

    assert (score > 0) - (score < 0) == expected_sign
    if expected_sign:
        assert abs(score) > WIN_SCORE // 2


def test_a_quicker_win_scores_higher_than_a_slower_one() -> None:
    """
    Prefer winning sooner, and losing later, by discounting each extra turn.
    """
    assert terminal_score(GameStatus.WHITE_WINS, Color.WHITE, 1) > terminal_score(
        GameStatus.WHITE_WINS, Color.WHITE, 3
    )
    assert terminal_score(GameStatus.WHITE_WINS, Color.BLACK, 3) > terminal_score(
        GameStatus.WHITE_WINS, Color.BLACK, 1
    )


def _board(*pieces: tuple[Coordinate, PieceKind, Color]) -> Board:
    """
    Build an 11x11 board holding exactly the given pieces.

    Arguments:
        pieces: Each piece as square, kind and colour.

    Returns:
        The board.
    """
    board = Board.empty(BoardDimensions(11, 11))
    for index, (square, kind, colour) in enumerate(pieces, start=1):
        board = board.with_piece(square, create_piece(index, kind, colour))
    return board


def test_a_piece_nearer_the_enemy_king_scores_higher() -> None:
    """
    Reward each square a piece closes on the opposing King.
    """
    kings = (
        (Coordinate(0, 0), PieceKind.KING, Color.WHITE),
        (Coordinate(10, 10), PieceKind.KING, Color.BLACK),
    )
    far = _board(*kings, (Coordinate(2, 2), PieceKind.ROOK, Color.WHITE))
    near = _board(*kings, (Coordinate(7, 7), PieceKind.ROOK, Color.WHITE))

    gain = evaluate(near, Color.WHITE) - evaluate(far, Color.WHITE)

    assert gain == pytest.approx(5 * PROXIMITY_WEIGHT)


def test_an_enemy_piece_near_your_king_counts_against_you() -> None:
    """
    Treat the opponent's pressure on your King as the mirror of your own.
    """
    kings = (
        (Coordinate(0, 0), PieceKind.KING, Color.WHITE),
        (Coordinate(10, 10), PieceKind.KING, Color.BLACK),
    )
    far = _board(*kings, (Coordinate(8, 8), PieceKind.ROOK, Color.BLACK))
    near = _board(*kings, (Coordinate(3, 3), PieceKind.ROOK, Color.BLACK))

    assert evaluate(near, Color.WHITE) < evaluate(far, Color.WHITE)


def test_a_king_earns_nothing_for_approaching_the_other_king() -> None:
    """
    Leave the Kings out of the pressure term, so the AI never walks its own King
    forward for a fraction of a point.
    """
    home = _board(
        (Coordinate(0, 0), PieceKind.KING, Color.WHITE),
        (Coordinate(10, 10), PieceKind.KING, Color.BLACK),
    )
    forward = _board(
        (Coordinate(6, 6), PieceKind.KING, Color.WHITE),
        (Coordinate(10, 10), PieceKind.KING, Color.BLACK),
    )

    assert evaluate(forward, Color.WHITE) == evaluate(home, Color.WHITE)
