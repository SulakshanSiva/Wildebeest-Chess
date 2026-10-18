from __future__ import annotations

from ..board import Board
from ..coordinates import Coordinate
from ..enums import Color
from ..move import Move
from .paralysis import is_paralysed


def moves_for_piece(board: Board, origin: Coordinate) -> tuple[Move, ...]:
    """
    List the moves of the piece on one square, honouring paralysis.

    A paralysed piece cannot move, but it can still be launched by a friendly
    Catapult, because the Catapult is the piece spending the turn. That case is
    covered by the Catapult's own moves, not by this one.

    Arguments:
        board: The board to read.
        origin: Square of the piece. Must be occupied.

    Returns:
        The piece's candidate moves, empty when it is paralysed.
    """
    if is_paralysed(board, origin):
        return ()
    return board.require_piece_at(origin).movement.candidates(board, origin)


def legal_moves(board: Board, side: Color) -> tuple[Move, ...]:
    """
    List every move available to a side.

    The rules have no check and no king safety, so legality is turn order plus
    each piece's own rule plus paralysis. A player may move into danger and
    simply lose, so no move is filtered for what it exposes.

    Arguments:
        board: The board to read.
        side: The colour whose moves are wanted.

    Returns:
        Every move of that colour's pieces, in reading order of the mover.
    """
    moves: list[Move] = []
    for square, _ in board.pieces(side):
        moves.extend(moves_for_piece(board, square))
    return tuple(moves)
