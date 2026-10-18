import pytest

from backend.domain.enums import Color, PieceKind
from backend.domain.errors import UnknownPieceSymbolError
from backend.domain.pieces.base import MovementRule
from backend.domain.pieces.registry import (
    SYMBOLS,
    build_rule,
    create_piece,
    describe_kinds,
    kind_for_symbol,
    symbol_for,
)

ALL_KINDS = list(PieceKind)
KIND_IDS = [kind.value for kind in ALL_KINDS]
BOTH_COLOURS = [Color.WHITE, Color.BLACK]
KIND_ARG = "kind"
UNUSED_LETTER = "Q"


def test_every_piece_kind_has_a_layout_symbol() -> None:
    """
    Leave no kind unrepresentable in a layout, and no symbol shared by two.

    The registry checks this at import; asserting it here makes the guarantee
    visible as a test rather than only as a startup failure.
    """
    assert set(SYMBOLS.values()) == set(PieceKind)
    assert len(SYMBOLS) == len(PieceKind)
    assert all(symbol.isupper() and len(symbol) == 1 for symbol in SYMBOLS)


@pytest.mark.parametrize(KIND_ARG, ALL_KINDS, ids=KIND_IDS)
def test_every_piece_kind_has_a_movement_rule(kind: PieceKind) -> None:
    """
    Build a rule for each kind, so no piece reaches play without one.

    Arguments:
        kind: The piece kind under test.
    """
    rule = build_rule(kind)

    assert isinstance(rule, MovementRule)


def test_describe_kinds_covers_every_kind_with_readable_text() -> None:
    """
    Describe all movement in plain language, which the variant metadata
    endpoint serves so the front end need not hard-code rule text.
    """
    descriptions = describe_kinds()

    assert set(descriptions) == set(PieceKind)
    assert all(text.strip() for text in descriptions.values())


def test_every_piece_has_a_specified_rule() -> None:
    """
    Describe every piece with a real rule, now that the Gorilla and Catapult
    are specified. No kind may fall back to an unspecified placeholder.
    """
    descriptions = describe_kinds()

    assert not any(text.startswith("UNSPECIFIED") for text in descriptions.values())
    assert "push" in descriptions[PieceKind.GORILLA]
    assert "fling" in descriptions[PieceKind.CATAPULT]


@pytest.mark.parametrize("symbol", sorted(SYMBOLS), ids=sorted(SYMBOLS))
def test_symbol_case_decides_colour(symbol: str) -> None:
    """
    Read an uppercase symbol as white and its lowercase twin as black.

    Arguments:
        symbol: The uppercase layout character under test.
    """
    upper_kind, upper_color = kind_for_symbol(symbol)
    lower_kind, lower_color = kind_for_symbol(symbol.lower())

    assert upper_color is Color.WHITE
    assert lower_color is Color.BLACK
    assert upper_kind is lower_kind is SYMBOLS[symbol]


@pytest.mark.parametrize(
    "symbol",
    [UNUSED_LETTER, "q", "A", "y", "", "PP", "Rr", "1", ".", "#", "*", " ", "-", "\n"],
    ids=[
        "upper-unused-letter",
        "lower-unused-letter",
        "upper-unused-a",
        "lower-unused-y",
        "empty",
        "two-letters",
        "mixed-case-pair",
        "digit",
        "normal-terrain",
        "hash-terrain",
        "star-terrain",
        "space",
        "dash",
        "newline",
    ],
)
def test_unknown_or_malformed_symbols_are_rejected(symbol: str) -> None:
    """
    Refuse anything that is not exactly one registered letter.

    Terrain characters are rejected here on purpose: the caller strips terrain
    before asking the registry what a piece is.

    Arguments:
        symbol: The input the registry must refuse.
    """
    with pytest.raises(UnknownPieceSymbolError):
        kind_for_symbol(symbol)


def test_rejected_symbol_error_carries_the_symbol_and_place() -> None:
    """
    Report where a bad symbol came from, so a layout can be corrected.
    """
    with pytest.raises(UnknownPieceSymbolError) as raised:
        kind_for_symbol(UNUSED_LETTER, 4, 7)

    assert raised.value.symbol == UNUSED_LETTER
    assert "(4, 7)" in str(raised.value)


@pytest.mark.parametrize(KIND_ARG, ALL_KINDS, ids=KIND_IDS)
@pytest.mark.parametrize("color", BOTH_COLOURS, ids=[color.value for color in BOTH_COLOURS])
def test_symbol_round_trips_through_a_piece(kind: PieceKind, color: Color) -> None:
    """
    Encode a piece to a layout character and decode it back unchanged.

    This is the per-piece half of the board round-trip: if it holds for every
    kind in both colours, rendering a board cannot lose a piece's identity.

    Arguments:
        kind: The piece kind under test.
        color: The side that owns the piece.
    """
    piece = create_piece(piece_id=1, kind=kind, color=color)
    symbol = symbol_for(piece)

    assert len(symbol) == 1
    assert symbol.isupper() is (color is Color.WHITE)
    assert kind_for_symbol(symbol) == (kind, color)


@pytest.mark.parametrize(KIND_ARG, ALL_KINDS, ids=KIND_IDS)
def test_created_pieces_carry_their_identity_kind_colour_and_rule(kind: PieceKind) -> None:
    """
    Assemble a ready-to-place piece with its rule already attached.

    Arguments:
        kind: The piece kind under test.
    """
    piece = create_piece(piece_id=42, kind=kind, color=Color.BLACK, has_moved=True)

    assert piece.piece_id == 42
    assert piece.kind is kind
    assert piece.color is Color.BLACK
    assert piece.has_moved is True
    assert piece.movement == build_rule(kind)


def test_pieces_of_a_kind_do_not_share_one_rule_object() -> None:
    """
    Hand out a fresh rule per piece, leaving room for per-piece configuration
    without one piece's change reaching another.
    """
    first = build_rule(PieceKind.ROOK)
    second = build_rule(PieceKind.ROOK)

    assert first is not second
    assert first == second
