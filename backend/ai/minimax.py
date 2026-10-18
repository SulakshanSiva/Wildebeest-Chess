from __future__ import annotations

from dataclasses import dataclass

from ..domain.board import Board
from ..domain.enums import Color, MoveAction
from ..domain.errors import GameOverError, InvariantViolation
from ..domain.game import Game
from ..domain.move import Move
from ..domain.rules.terrain import TransporterLinks
from ..domain.rules.turn import TurnResult, resolve_turn
from .evaluation import WIN_SCORE, evaluate, terminal_score
from .piece_values import value_of

DEFAULT_DEPTH = 2
# Beyond any reachable score, so the first real score always replaces it.
INFINITY = WIN_SCORE * 10
REMOVING_ACTIONS = (MoveAction.CAPTURE, MoveAction.CRUSH, MoveAction.FLING)


class MinimaxPlayer:
    """
    A computer player that picks moves with the Minimax algorithm.

    Minimax imagines every move it could make, every reply the opponent could
    make to each, and so on, to a fixed depth. It assumes the opponent always
    picks the reply that is worst for the AI, and chooses the move whose worst
    case is best. Alpha-beta pruning skips branches that cannot change that
    choice, which gives the same answer as plain Minimax in far less time.

    Each step of the search plays a whole turn through the same rules a human
    move uses, after-effects included. In this game poison, a Golf Cart rampage
    or a Joey explosion can take a King after the move that caused it, so a
    search over bare moves would walk straight into them.
    """

    def __init__(self, depth: int = DEFAULT_DEPTH) -> None:
        """
        Build a player that looks a fixed number of turns ahead.

        Arguments:
            depth: Turns to look ahead, counting the AI's own move as the first.
                Each extra turn multiplies the work by roughly the number of
                legal moves, so small depths are the practical ones.
        """
        if depth < 1:
            raise ValueError(f"search depth must be at least 1, got {depth}")
        self._depth = depth

    @property
    def depth(self) -> int:
        """
        Give how many turns ahead this player looks.

        Returns:
            The search depth in turns.
        """
        return self._depth

    def choose_move(self, game: Game) -> Move:
        """
        Pick the best move for the side to move.

        Ties go to whichever equal move comes first, so the same position
        always gives the same move.

        Arguments:
            game: The game to move in. Must not be over.

        Returns:
            One of the game's legal moves.
        """
        if game.status.is_over:
            raise GameOverError

        search = _Search(me=game.side_to_move, links=game.variant.transporter_links)
        best_move: Move | None = None
        best_score = -INFINITY
        alpha = -INFINITY

        for move in _ordered(game.position.board, game.legal_moves()):
            turn = resolve_turn(game.position, move, search.links)
            score = search.minimax(turn, self._depth - 1, alpha, INFINITY, 1)
            if best_move is None or score > best_score:
                best_move, best_score = move, score
            alpha = max(alpha, best_score)

        if best_move is None:
            raise InvariantViolation("an active game offered no legal move to search")
        return best_move


@dataclass(frozen=True, slots=True)
class _Search:
    """
    The facts that stay fixed for one whole search.

    Bundled so the recursive step only carries what changes from call to call.

    Attributes:
        me: The colour the AI is playing.
        links: The variant's transporter pad mapping.
    """

    me: Color
    links: TransporterLinks

    def minimax(self, turn: TurnResult, depth: int, alpha: int, beta: int, ply: int) -> int:
        """
        Score a position by searching the moves that follow it.

        On the AI's turn the best-scoring move is assumed; on the opponent's turn
        the worst-scoring one is, since the opponent is trying to win.

        Arguments:
            turn: The result of the move that produced this position.
            depth: Turns still to look ahead.
            alpha: The best score the AI is already guaranteed elsewhere.
            beta: The best score the opponent is already guaranteed elsewhere.
            ply: Turns since the root, used to prefer quicker wins.

        Returns:
            The position's score from the AI's point of view.
        """
        if turn.status.is_over:
            return terminal_score(turn.status, self.me, ply)
        if depth == 0:
            return evaluate(turn.position.board, self.me)

        moves = _ordered(turn.position.board, turn.next_moves)

        if turn.position.side_to_move is self.me:
            best = -INFINITY
            for move in moves:
                child = resolve_turn(turn.position, move, self.links)
                best = max(best, self.minimax(child, depth - 1, alpha, beta, ply + 1))
                alpha = max(alpha, best)
                # The opponent already has a better option elsewhere, so it will
                # never let play reach here.
                if alpha >= beta:
                    break
            return best

        worst = INFINITY
        for move in moves:
            child = resolve_turn(turn.position, move, self.links)
            worst = min(worst, self.minimax(child, depth - 1, alpha, beta, ply + 1))
            beta = min(beta, worst)
            # The AI already has a better option elsewhere, so it will never
            # choose to come here.
            if alpha >= beta:
                break
        return worst


def _ordered(board: Board, moves: tuple[Move, ...]) -> list[Move]:
    """
    Sort moves so the ones that take the most valuable piece come first.

    Alpha-beta pruning cuts the most when strong moves are searched early, and a
    capture is the cheapest sign of a strong move. Sorting never changes how
    good the chosen move is, only how quickly it is found; among equally good
    moves, the first one searched is chosen. The sort is stable, so equal
    captures keep the generator's order and the choice stays deterministic.

    Arguments:
        board: The board the moves are played on.
        moves: The moves to sort.

    Returns:
        The same moves, most valuable capture first.
    """
    return sorted(moves, key=lambda move: -_victim_value(board, move))


def _victim_value(board: Board, move: Move) -> int:
    """
    Give the value of the piece a move removes, if any.

    Arguments:
        board: The board the move is played on.
        move: The move to price.

    Returns:
        The victim's value, or zero for a move that removes nothing.
    """
    if move.action not in REMOVING_ACTIONS:
        return 0
    victim = board.piece_at(move.destination)
    return 0 if victim is None else value_of(victim.kind)
