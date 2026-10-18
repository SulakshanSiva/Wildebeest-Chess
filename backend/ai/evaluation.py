from __future__ import annotations

from ..domain.board import Board
from ..domain.enums import Color, GameStatus
from .piece_values import value_of

# Larger than any material total can reach, so a win always outranks material.
WIN_SCORE = 1_000_000


def evaluate(board: Board, perspective: Color) -> int:
    """
    Score a board by material, from one side's point of view.

    Adds the value of every piece the side owns and subtracts the value of every
    piece the opponent owns. Positive means the side is ahead.

    Arguments:
        board: The board to score.
        perspective: The colour the score is for.

    Returns:
        The material balance, in the same 0-to-10 units as the piece values.
    """
    score = 0
    for _, piece in board.pieces():
        worth = value_of(piece.kind)
        score += worth if piece.color is perspective else -worth
    return score


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
