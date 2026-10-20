from __future__ import annotations

from ..domain.board import Board
from ..domain.coordinates import Coordinate
from ..domain.enums import Color, GameStatus
from .piece_values import value_of

# Larger than any material total can reach, so a win always outranks material.
WIN_SCORE = 1_000_000

# Score per square closer a piece stands to the enemy King. Small next to a pawn
# (1), so it only breaks ties between moves that are equal on material.
PROXIMITY_WEIGHT = 0.2


def evaluate(board: Board, perspective: Color) -> float:
    """
    Score a board by material and by pressure on the enemy King.

    Material: add the value of every piece the side owns, subtract the value of
    every piece the opponent owns. Pressure: each non-royal piece earns a little
    for every square it stands closer to the opposing King, so between moves of
    equal material the AI prefers the one that advances. The opponent's pieces
    count against the side the same way, by how close they are to its King.

    Kings themselves earn no pressure, so the AI never marches its own King
    towards the enemy for a fraction of a point.

    Arguments:
        board: The board to score.
        perspective: The colour the score is for.

    Returns:
        Positive when the side is ahead, in pawns.
    """
    kings = {piece.color: square for square, piece in board.pieces() if piece.kind.is_royal}
    # The farthest two squares can be apart, so the closest piece earns the most.
    reach = max(board.rows, board.columns) - 1

    score = 0.0
    for square, piece in board.pieces():
        mine = piece.color is perspective
        worth: float = value_of(piece.kind)

        target = kings.get(piece.color.opponent)
        if target is not None and not piece.kind.is_royal:
            worth += PROXIMITY_WEIGHT * (reach - _distance(square, target))

        score += worth if mine else -worth
    return score


def _distance(a: Coordinate, b: Coordinate) -> int:
    """
    Count the King moves between two squares.

    Arguments:
        a: One square.
        b: The other square.

    Returns:
        The larger of the row and column differences.
    """
    return max(abs(a.row - b.row), abs(a.column - b.column))


def terminal_score(status: GameStatus, perspective: Color, ply: int) -> int:
    """
    Score a finished game from one side's point of view.

    The ply adjustment makes a quick win worth more than a slow one, and a slow
    loss worth more than a quick one, so the AI finishes a won game and drags
    out a lost one instead of being indifferent between them.

    Arguments:
        status: How the game ended.
        perspective: The colour the score is for.
        ply: How many turns into the search the game ended.

    Returns:
        Zero for a draw, close to WIN_SCORE for a win, close to minus it for a loss.
    """
    if status is GameStatus.DRAW:
        return 0
    winner = Color.WHITE if status is GameStatus.WHITE_WINS else Color.BLACK
    if winner is perspective:
        return WIN_SCORE - ply
    return -(WIN_SCORE - ply)
