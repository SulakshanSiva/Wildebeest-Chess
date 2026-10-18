from __future__ import annotations

from ..board import Board
from ..enums import MoveAction
from ..errors import InvariantViolation
from ..move import Move


def apply_move(board: Board, move: Move) -> Board:
    """
    Apply one move to a board and return the result.

    This is the move alone. After-effects run separately, afterwards, because
    the rules define them as a phase that follows the player's move.

    Who counts as having moved matters for the pawn's double step. The actor
    marks as moved when it steps, but a piece that is shoved by a Gorilla or
    flung by a Catapult did not spend its own turn, so it keeps its first move,
    as a transported piece does.

    Arguments:
        board: The board before the move. Never modified.
        move: A legal move for that board.

    Returns:
        A new board with the move resolved.
    """
    action = move.action

    if action is MoveAction.MOVE:
        return board.with_piece_relocated(move.origin, move.destination)

    if action is MoveAction.CAPTURE:
        cleared = board.without_piece(move.destination)
        return cleared.with_piece_relocated(move.origin, move.destination)

    if action is MoveAction.PUSH:
        return _apply_push(board, move)

    if action is MoveAction.CRUSH:
        cleared = board.without_piece(move.destination)
        return cleared.with_piece_relocated(move.origin, move.destination)

    if action is MoveAction.FLING:
        return _apply_fling(board, move)

    raise InvariantViolation(f"no resolution defined for move action {action.name}")


def _apply_push(board: Board, move: Move) -> Board:
    """
    Resolve a Gorilla push: the occupant steps aside, then the Gorilla steps in.

    The occupant has to leave first, otherwise the Gorilla's step would land on
    an occupied square.

    Arguments:
        board: The board before the push.
        move: A PUSH move carrying its displacement.

    Returns:
        A new board with both pieces moved.
    """
    if move.displaced is None:
        raise InvariantViolation("a PUSH move must carry the displacement it causes")

    shoved = board.with_piece_relocated(
        move.displaced.origin, move.displaced.destination, mark_moved=False
    )
    return shoved.with_piece_relocated(move.origin, move.destination)


def _apply_fling(board: Board, move: Move) -> Board:
    """
    Resolve a Catapult fling: the passenger leaves, and may capture on landing.

    The Catapult does not move. The passenger is placed unchanged, because the
    Catapult spent the turn and not the passenger.

    Arguments:
        board: The board before the fling.
        move: A FLING move naming the catapult, passenger and landing.

    Returns:
        A new board with the passenger relocated and any victim removed.
    """
    landing = move.destination
    cleared = board if board.is_empty(landing) else board.without_piece(landing)
    return cleared.with_piece_relocated(move.origin, landing, mark_moved=False)
