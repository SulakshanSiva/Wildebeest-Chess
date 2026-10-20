from __future__ import annotations

import pytest

from backend.ai.piece_values import PIECE_VALUES, value_of
from backend.domain.enums import PieceKind

# The heuristics from the original Wildebeest player, which the user asked to keep.
ORIGINAL_VALUES = {
    PieceKind.KING: 1000,
    PieceKind.JET_PACK_KING: 1000,
    PieceKind.JOEY: 50,
    PieceKind.SERPENT: 10,
    PieceKind.GORILLA: 5,
    PieceKind.OLD_WOMAN: 5,
    PieceKind.GOLF_CART: 5,
    PieceKind.GRAND_EMPRESS: 6,
    PieceKind.BEEKEEPER: 6,
    PieceKind.BISHOP: 4,
    PieceKind.ROOK: 3,
    PieceKind.KNIGHT: 3,
    PieceKind.CATAPULT: 3,
    PieceKind.PAWN: 1,
    PieceKind.TIME_MACHINE: 1,
}


@pytest.mark.parametrize("kind", list(PieceKind), ids=lambda kind: kind.value)
def test_every_piece_has_a_positive_whole_number_value(kind: PieceKind) -> None:
    """
    Price every piece kind, so none is left out of the evaluation.

    Arguments:
        kind: The piece kind under test.
    """
    value = value_of(kind)

    assert isinstance(value, int)
    assert value > 0


def test_the_values_are_the_original_players() -> None:
    """
    Keep exactly the heuristics the original Wildebeest player used.
    """
    assert PIECE_VALUES == ORIGINAL_VALUES


def test_a_king_outweighs_one_of_every_other_kind_combined() -> None:
    """
    Value a King above one of each other piece kind put together.
    """
    others = sum(value for kind, value in PIECE_VALUES.items() if not kind.is_royal)

    assert value_of(PieceKind.KING) > others
    assert value_of(PieceKind.JET_PACK_KING) == value_of(PieceKind.KING)


def test_the_pawn_and_time_machine_are_the_weakest() -> None:
    """
    Keep the pawn as the unit every other value is measured against.
    """
    weakest = min(PIECE_VALUES.values())

    assert value_of(PieceKind.PAWN) == weakest
    assert value_of(PieceKind.TIME_MACHINE) == weakest
