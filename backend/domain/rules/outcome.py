from __future__ import annotations

from ..board import Board
from ..enums import Color, GameStatus


def surviving_royals(board: Board) -> frozenset[Color]:
    """
    Give the colours that still have a King on the board.

    A King with a Jet Pack counts, because the rules treat it as a King.

    Arguments:
        board: The board to read.

    Returns:
        The colours with at least one royal piece remaining.
    """
    return frozenset(piece.color for _, piece in board.pieces() if piece.kind.is_royal)


def evaluate_status(board: Board) -> GameStatus:
    """
    Decide the outcome implied by a board.

    The rules define a win as capturing the opposing King rather than as
    checkmate, so this is a question about which Kings are still standing. It
    must be asked after the after-effects have run, because poisoning, a Golf
    Cart rampage, an explosion and a crush can all take a King.

    Arguments:
        board: The board to judge, after all after-effects.

    Returns:
        The game status. A draw when both Kings fell together, which the rules
        call out explicitly for simultaneous capture during after-effects.
    """
    survivors = surviving_royals(board)

    if Color.WHITE in survivors and Color.BLACK in survivors:
        return GameStatus.ACTIVE
    if Color.WHITE in survivors:
        return GameStatus.WHITE_WINS
    if Color.BLACK in survivors:
        return GameStatus.BLACK_WINS
    return GameStatus.DRAW
