from __future__ import annotations

import pytest

from backend.ai.piece_values import PIECE_VALUES, value_of
from backend.domain.enums import PieceKind

SCALE_TOP = 10


@pytest.mark.parametrize("kind", list(PieceKind), ids=lambda kind: kind.value)
def test_every_piece_has_a_whole_number_value_out_of_ten(kind: PieceKind) -> None:
    """
    Rate every piece kind on the 0-to-10 scale, so none is left unpriced.

    Arguments:
        kind: The piece kind under test.
    """
    value = value_of(kind)

    assert isinstance(value, int)
    assert 0 <= value <= SCALE_TOP


def test_both_kings_top_the_scale() -> None:
    """
    Put the pieces whose loss ends the game at the top.
    """
    assert value_of(PieceKind.KING) == SCALE_TOP
    assert value_of(PieceKind.JET_PACK_KING) == SCALE_TOP


def test_the_grand_empress_is_the_strongest_ordinary_piece() -> None:
    """
    Rank the Knight-plus-Queen-plus-poison piece above every non-royal piece.
    """
    others = [
        value
        for kind, value in PIECE_VALUES.items()
        if not kind.is_royal and kind is not PieceKind.GRAND_EMPRESS
    ]

    assert value_of(PieceKind.GRAND_EMPRESS) > max(others)


def test_the_pawn_is_the_weakest_piece() -> None:
    """
    Keep the pawn as the unit every other value is measured against.
    """
    assert value_of(PieceKind.PAWN) == min(PIECE_VALUES.values())


def test_the_chess_pieces_keep_their_chess_order() -> None:
    """
    Rank the pieces that move as in chess the way chess ranks them.
    """
    assert value_of(PieceKind.ROOK) > value_of(PieceKind.BISHOP)
    assert value_of(PieceKind.BISHOP) == value_of(PieceKind.KNIGHT)
    assert value_of(PieceKind.KNIGHT) > value_of(PieceKind.PAWN)
