from __future__ import annotations

from ..domain.enums import PieceKind

# Worth of each piece out of 10, judged by what it can do in this variant rather
# than by its chess namesake.
PIECE_VALUES: dict[PieceKind, int] = {
    # Losing either one loses the game, so both Kings top the scale. Both sides
    # always hold one while the game is live, so the values cancel out.
    PieceKind.KING: 10,
    PieceKind.JET_PACK_KING: 10,
    # Knight, Queen and poison in one piece: the strongest piece in the game.
    PieceKind.GRAND_EMPRESS: 10,
    # Standard chess values: these move exactly as they do in chess.
    PieceKind.ROOK: 5,
    PieceKind.KNIGHT: 3,
    PieceKind.BISHOP: 3,
    # Moves one square and never captures, but every adjacent enemy dies each
    # turn, so it threatens up to eight pieces at once.
    PieceKind.SERPENT: 5,
    # Cannot be captured by an ordinary move, and shoves or crushes whatever it
    # steps into, friend or foe.
    PieceKind.GORILLA: 4,
    # Cannot capture, but launches friendly pieces any distance across the board.
    PieceKind.CATAPULT: 4,
    # Freezes every adjacent enemy for as long as it stands beside them.
    PieceKind.BEEKEEPER: 4,
    # Cannot move, but charges its own side's Golf Cart every turn it survives.
    PieceKind.TIME_MACHINE: 4,
    # A one-square mover whose real worth is turning into a Grand Empress when
    # she shields a neighbour from poison.
    PieceKind.OLD_WOMAN: 3,
    # Confined to its home rows, but a charged cart clears a whole column.
    PieceKind.GOLF_CART: 3,
    # A one-square mover that explodes when its row count divides by five,
    # often taking friendly neighbours with it.
    PieceKind.JOEY: 2,
    # The unit everything else is measured against. A pawn that reaches the far
    # row becomes a Time Machine.
    PieceKind.PAWN: 1,
}


def value_of(kind: PieceKind) -> int:
    """
    Give the heuristic worth of a piece kind.

    Arguments:
        kind: The piece kind to price.

    Returns:
        Its value on a scale of 0 to 10.
    """
    return PIECE_VALUES[kind]
