from __future__ import annotations

import pytest

from backend.domain.enums import PieceKind

ROYAL_KINDS = {PieceKind.KING, PieceKind.JET_PACK_KING}
HOVERING_KINDS = {PieceKind.JET_PACK_KING}
POISONING_KINDS = {PieceKind.SERPENT, PieceKind.GRAND_EMPRESS}


@pytest.mark.parametrize("kind", list(PieceKind), ids=lambda kind: kind.value)
def test_only_the_two_kings_are_royal(kind: PieceKind) -> None:
    """
    Treat the Jet Pack King as a King, since the rules say King includes it.

    Arguments:
        kind: The piece kind under test.
    """
    assert kind.is_royal is (kind in ROYAL_KINDS)


@pytest.mark.parametrize("kind", list(PieceKind), ids=lambda kind: kind.value)
def test_only_the_jet_pack_king_hovers(kind: PieceKind) -> None:
    """
    Mark exactly one kind as hovering, which gates pushing and flinging.

    Arguments:
        kind: The piece kind under test.
    """
    assert kind.is_hovering is (kind in HOVERING_KINDS)


@pytest.mark.parametrize("kind", list(PieceKind), ids=lambda kind: kind.value)
def test_the_serpent_and_grand_empress_poison(kind: PieceKind) -> None:
    """
    Give the Grand Empress the Serpent's poison, as the rules confirm.

    Arguments:
        kind: The piece kind under test.
    """
    assert kind.poisons is (kind in POISONING_KINDS)


def test_a_hovering_piece_is_also_royal() -> None:
    """
    Record the overlap: the only hovering piece is a King, so it is protected
    both as royalty and as a hovering unit.
    """
    for kind in PieceKind:
        if kind.is_hovering:
            assert kind.is_royal
