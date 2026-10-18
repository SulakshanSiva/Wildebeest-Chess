from __future__ import annotations

from ..board import Board
from ..coordinates import ALL_DIRECTIONS, Coordinate
from ..enums import PieceKind

IMMUNE_TO_PARALYSIS = (PieceKind.GOLF_CART, PieceKind.TIME_MACHINE)


def is_paralysed(board: Board, square: Coordinate) -> bool:
    """
    Say whether the piece on a square is held by an enemy BeeKeeper's swarm.

    The swarm is permanent and is released before the game starts, so a piece
    is paralysed exactly while it stands next to an opposing BeeKeeper. A piece
    may move through a swarmed square freely; it is only stopped when it starts
    its turn in one.

    Arguments:
        board: The board to read.
        square: Square of the piece to test. Must be occupied.

    Returns:
        True when an opposing BeeKeeper stands adjacent and the piece can be
        paralysed at all.
    """
    piece = board.require_piece_at(square)
    if piece.kind in IMMUNE_TO_PARALYSIS:
        return False

    for direction in ALL_DIRECTIONS:
        neighbour = square.shifted(direction)
        if neighbour is None or not board.contains(neighbour):
            continue
        occupant = board.piece_at(neighbour)
        if (
            occupant is not None
            and occupant.kind is PieceKind.BEEKEEPER
            and occupant.color is not piece.color
        ):
            return True

    return False
