from __future__ import annotations

from dataclasses import dataclass

from ..enums import EndReason, GameStatus
from ..move import Move
from ..position import Position
from .after_effects import AfterEffectReport, run_after_effects
from .move_applier import apply_move
from .move_generator import legal_moves
from .outcome import evaluate_status
from .terrain import TransporterLinks


@dataclass(frozen=True, slots=True)
class TurnResult:
    """
    Everything a single turn produced.

    Attributes:
        position: The position after the move, the after-effects and the
            hand-over of the turn.
        status: The verdict on that position.
        end_reason: Why the game ended, or None while it is active.
        report: What the after-effects did.
        next_moves: The moves available to the side now to move, empty once the
            game is over. Returned because working them out is how a game with
            no legal moves is detected, and a caller usually wants them next.
    """

    position: Position
    status: GameStatus
    end_reason: EndReason | None
    report: AfterEffectReport
    next_moves: tuple[Move, ...]


def resolve_turn(position: Position, move: Move, links: TransporterLinks) -> TurnResult:
    """
    Play one move through the whole turn and judge the result.

    The order is the rules' order: the move, the five after-effect phases, the
    hand-over, then the verdict. The verdict comes last because poison, a
    rampage, an explosion or a crush can take a King as surely as a capture.

    This does not check that the move is legal. The Game aggregate validates
    before calling it, and the AI search only ever passes moves it generated.

    Arguments:
        position: The position the move is played from. Never modified.
        move: A legal move for the side to move.
        links: The variant's transporter pad mapping.

    Returns:
        The resulting position, verdict and the next side's moves.
    """
    moved = apply_move(position.board, move)
    report = run_after_effects(moved, links)
    after = position.with_board(report.board).with_turn_passed()

    status = evaluate_status(report.board)
    if status.is_over:
        return TurnResult(after, status, EndReason.KING_CAPTURED, report, ())

    next_moves = legal_moves(report.board, after.side_to_move)
    if not next_moves:
        # The rules never address a side with nothing to play. Treated as a
        # draw so a game cannot hang.
        return TurnResult(after, GameStatus.DRAW, EndReason.NO_LEGAL_MOVES, report, ())

    return TurnResult(after, GameStatus.ACTIVE, None, report, next_moves)
