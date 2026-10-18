from __future__ import annotations

import pytest

from backend.ai.evaluation import WIN_SCORE, evaluate, terminal_score
from backend.ai.piece_values import value_of
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, GameStatus, PieceKind
from backend.domain.variant import Variant

BLACK_ROOK = Coordinate(10, 0)


def test_the_opening_position_is_level() -> None:
    """
    Score the symmetric starting position as even for both sides.
    """
    board = Variant().build_board()

    assert evaluate(board, Color.WHITE) == 0
    assert evaluate(board, Color.BLACK) == 0


def test_losing_a_piece_moves_the_score_by_its_value() -> None:
    """
    Credit White and debit Black by exactly a rook when Black loses one.
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
