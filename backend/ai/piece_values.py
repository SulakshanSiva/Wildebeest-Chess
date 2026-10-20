from __future__ import annotations

from ..domain.enums import PieceKind

# Worth of each piece, in pawns, from the original Wildebeest player.
PIECE_VALUES: dict[PieceKind, int] = {
    # Losing either one loses the game, so both dwarf every other piece. Both
    # sides hold one while the game is live, so in practice they cancel out.
    PieceKind.KING: 1000,
    PieceKind.JET_PACK_KING: 1000,
    # An explosion can take a King, so Joey outweighs every ordinary piece.
    PieceKind.JOEY: 50,
    # Every adjacent enemy dies to its poison each turn.
    PieceKind.SERPENT: 10,
    PieceKind.GRAND_EMPRESS: 6,
    PieceKind.BEEKEEPER: 6,
    PieceKind.GORILLA: 5,
    PieceKind.OLD_WOMAN: 5,
    PieceKind.GOLF_CART: 5,
    PieceKind.BISHOP: 4,
    PieceKind.ROOK: 3,
    PieceKind.KNIGHT: 3,
    PieceKind.CATAPULT: 3,
    PieceKind.PAWN: 1,
    PieceKind.TIME_MACHINE: 1,
}


def value_of(kind: PieceKind) -> int:
    """
    Give the heuristic worth of a piece kind.

    Arguments:
        kind: The piece kind to price.

    Returns:
        Its value in pawns.
    """
    return PIECE_VALUES[kind]
