from __future__ import annotations

from collections.abc import Callable

from ..coordinates import ALL_DIRECTIONS, DIAGONAL, KNIGHT_LEAPS, ORTHOGONAL, SIDEWAYS
from ..enums import Color, PieceKind
from ..errors import PieceNotRegisteredError, UnknownPieceSymbolError
from .base import MovementRule, Piece
from .mechanics import EdgeRowsOnlyRule, FlingRule, PushRule
from .movement import (
    CompositeRule,
    LeapRule,
    NoMovementRule,
    PawnRule,
    SlideRule,
    step_rule,
)

# King, Joey, Old Woman and BeeKeeper all move identically today. They stay
# distinct kinds because they may yet differ, but they share one rule.
_ADJACENT_STEPPERS = (
    PieceKind.KING,
    PieceKind.JOEY,
    PieceKind.OLD_WOMAN,
    PieceKind.BEEKEEPER,
)

_RULE_FACTORIES: dict[PieceKind, Callable[[], MovementRule]] = {
    PieceKind.PAWN: PawnRule,
    PieceKind.ROOK: lambda: SlideRule(directions=ORTHOGONAL),
    PieceKind.BISHOP: lambda: SlideRule(directions=DIAGONAL),
    # Confirmed: a king with a jet pack moves exactly like a bishop. Identical
    # to BISHOP above on purpose, not by oversight.
    PieceKind.JET_PACK_KING: lambda: SlideRule(directions=DIAGONAL),
    PieceKind.KNIGHT: lambda: LeapRule(offsets=KNIGHT_LEAPS),
    # Moves one square in any direction but has no capture branch at all.
    PieceKind.SERPENT: lambda: step_rule(ALL_DIRECTIONS, can_capture=False),
    # Moves and captures left and right, and only on the top and bottom rows.
    PieceKind.GOLF_CART: lambda: EdgeRowsOnlyRule(inner=step_rule(SIDEWAYS)),
    PieceKind.GRAND_EMPRESS: lambda: CompositeRule(
        rules=(
            LeapRule(offsets=KNIGHT_LEAPS),
            SlideRule(directions=ALL_DIRECTIONS),
        )
    ),
    PieceKind.TIME_MACHINE: lambda: NoMovementRule(
        reason="the Time Machine cannot move or capture"
    ),
    PieceKind.GORILLA: PushRule,
    PieceKind.CATAPULT: FlingRule,
}

_RULE_FACTORIES.update({kind: lambda: step_rule(ALL_DIRECTIONS) for kind in _ADJACENT_STEPPERS})

# Uppercase symbol to kind; lowercase is the same kind in black.
SYMBOLS: dict[str, PieceKind] = {
    "P": PieceKind.PAWN,
    "B": PieceKind.BISHOP,
    "N": PieceKind.KNIGHT,
    "R": PieceKind.ROOK,
    "K": PieceKind.KING,
    "W": PieceKind.JET_PACK_KING,
    "J": PieceKind.JOEY,
    "H": PieceKind.TIME_MACHINE,
    "S": PieceKind.SERPENT,
    "O": PieceKind.OLD_WOMAN,
    "E": PieceKind.GRAND_EMPRESS,
    "X": PieceKind.GOLF_CART,
    "Z": PieceKind.BEEKEEPER,
    "G": PieceKind.GORILLA,
    "C": PieceKind.CATAPULT,
}

_KIND_TO_SYMBOL: dict[PieceKind, str] = {kind: symbol for symbol, kind in SYMBOLS.items()}


def _verify_registry() -> None:
    """
    Check that every piece kind has a layout symbol and a movement rule.

    Run at import, so an unregistered piece is a startup failure rather than a
    missing-key error in the middle of a game.
    """
    missing_symbols = set(PieceKind) - set(_KIND_TO_SYMBOL)
    if missing_symbols:
        names = sorted(kind.value for kind in missing_symbols)
        raise PieceNotRegisteredError(f"piece kinds with no layout symbol: {names}")

    missing_rules = set(PieceKind) - set(_RULE_FACTORIES)
    if missing_rules:
        names = sorted(kind.value for kind in missing_rules)
        raise PieceNotRegisteredError(f"piece kinds with no movement rule: {names}")

    if len(SYMBOLS) != len(_KIND_TO_SYMBOL):
        raise PieceNotRegisteredError("two layout symbols map to the same piece kind")


_verify_registry()


def build_rule(kind: PieceKind) -> MovementRule:
    """
    Build the movement rule for a piece kind.

    Arguments:
        kind: The kind whose rule is wanted.

    Returns:
        A fresh movement rule. Rules are frozen and could be shared, but a
        per-piece instance leaves room for piece-specific configuration later.
    """
    factory = _RULE_FACTORIES.get(kind)
    if factory is None:
        raise PieceNotRegisteredError(f"no movement rule registered for {kind.value}")
    return factory()


def kind_for_symbol(symbol: str, row: int = 0, column: int = 0) -> tuple[PieceKind, Color]:
    """
    Decode one layout character into a piece kind and a colour.

    Arguments:
        symbol: A single layout character. Case encodes colour.
        row: Row the symbol came from, for the error message.
        column: Column the symbol came from, for the error message.

    Returns:
        The kind and the colour the character denotes.
    """
    if len(symbol) != 1 or not symbol.isalpha():
        raise UnknownPieceSymbolError(symbol, row, column)

    kind = SYMBOLS.get(symbol.upper())
    if kind is None:
        raise UnknownPieceSymbolError(symbol, row, column)

    return kind, Color.WHITE if symbol.isupper() else Color.BLACK


def symbol_for(piece: Piece) -> str:
    """
    Encode a piece back into its layout character.

    Arguments:
        piece: The piece to encode.

    Returns:
        An uppercase character for white, lowercase for black.
    """
    symbol = _KIND_TO_SYMBOL[piece.kind]
    return symbol if piece.color is Color.WHITE else symbol.lower()


def create_piece(
    piece_id: int,
    kind: PieceKind,
    color: Color,
    *,
    has_moved: bool = False,
) -> Piece:
    """
    Build a piece with its movement rule attached.

    Arguments:
        piece_id: Stable identity for this piece.
        kind: What type of piece to build.
        color: Which side owns it.
        has_moved: Whether it has already moved.

    Returns:
        A ready-to-place piece.
    """
    return Piece(
        piece_id=piece_id,
        kind=kind,
        color=color,
        movement=build_rule(kind),
        has_moved=has_moved,
    )


def describe_kinds() -> dict[PieceKind, str]:
    """
    Summarise every piece kind's movement.

    Feeds the variant metadata endpoint so the front end does not hard-code
    rule text.

    Returns:
        A mapping of kind to plain-language movement description.
    """
    return {kind: build_rule(kind).description for kind in PieceKind}
