from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..coordinates import Coordinate, Offset
from ..move import Move
from .base import MovementRule

if TYPE_CHECKING:
    from ..board import Board


@dataclass(frozen=True, slots=True)
class LeapRule(MovementRule):
    """
    Jump to each of a fixed set of offsets, ignoring what is in between.

    This is the single mechanism behind both stepping and leaping pieces. A
    king's one-square step and a knight's L are the same operation with
    different offset tables, because neither inspects the squares it crosses.

    Attributes:
        offsets: Where the piece may land, relative to its own square.
        can_capture: Whether landing on an enemy removes it. False gives the
            Serpent, which cannot capture at all.
    """

    offsets: tuple[Offset, ...]
    can_capture: bool = True

    def candidates(self, board: Board, origin: Coordinate) -> tuple[Move, ...]:
        """
        List each reachable offset square.

        Arguments:
            board: The board to read.
            origin: Square of the leaping piece.

        Returns:
            A move for every offset that lands on an empty square, plus
            captures when this rule allows them.
        """
        piece = board.require_piece_at(origin)
        moves: list[Move] = []

        for offset in self.offsets:
            destination = origin.shifted(offset)
            if destination is None or not board.contains(destination):
                continue

            if board.is_empty(destination):
                moves.append(Move.simple(origin, destination, capture=False))
            elif (
                self.can_capture and board.capturable_enemy_at(destination, piece.color) is not None
            ):
                moves.append(Move.simple(origin, destination, capture=True))

        return tuple(moves)

    @property
    def description(self) -> str:
        """
        Summarise this rule in plain language.

        Returns:
            Whether the piece steps or leaps, and whether it can capture.
        """
        verb = "steps" if all(offset.is_adjacent_step for offset in self.offsets) else "leaps"
        suffix = "" if self.can_capture else ", cannot capture"
        return f"{verb} to {len(self.offsets)} squares{suffix}"


@dataclass(frozen=True, slots=True)
class SlideRule(MovementRule):
    """
    Travel along each direction until blocked or off the board.

    Stops before a friendly piece and on an enemy one.

    Attributes:
        directions: Directions to travel along.
        max_distance: Furthest reach, or None to run to the edge.
    """

    directions: tuple[Offset, ...]
    max_distance: int | None = None

    def candidates(self, board: Board, origin: Coordinate) -> tuple[Move, ...]:
        """
        List each square reachable along an unobstructed line.

        Arguments:
            board: The board to read.
            origin: Square of the sliding piece.

        Returns:
            A move for each empty square along each direction, plus the capture
            that terminates a line.
        """
        piece = board.require_piece_at(origin)
        moves: list[Move] = []
        reach = self.max_distance
        if reach is None:
            reach = max(board.rows, board.columns)

        for direction in self.directions:
            for distance in range(1, reach + 1):
                destination = origin.shifted(direction, distance)
                if destination is None or not board.contains(destination):
                    break

                if board.is_empty(destination):
                    moves.append(Move.simple(origin, destination, capture=False))
                    continue

                # Occupied: capture an enemy that can be captured, then stop either way.
                if board.capturable_enemy_at(destination, piece.color) is not None:
                    moves.append(Move.simple(origin, destination, capture=True))
                break

        return tuple(moves)

    @property
    def description(self) -> str:
        """
        Summarise this rule in plain language.

        Returns:
            How many directions the piece slides along, and how far.
        """
        reach = "any distance" if self.max_distance is None else f"up to {self.max_distance}"
        return f"slides {reach} along {len(self.directions)} directions"


@dataclass(frozen=True, slots=True)
class PawnRule(MovementRule):
    """
    Forward-only movement with diagonal-only capture.

    Direction comes from the colour, so one rule serves both sides. The double
    step requires both intervening squares clear and is offered only to an
    unmoved pawn, and the pawn cannot capture straight ahead.

    En passant is not allowed by the rules. Promotion is not part of a move: a
    pawn on the far row becomes a Time Machine in the after-effects.

    Attributes:
        double_step_distance: How far the unmoved double step travels.
    """

    double_step_distance: int = 2

    def candidates(self, board: Board, origin: Coordinate) -> tuple[Move, ...]:
        """
        List the pawn's advances and diagonal captures.

        Arguments:
            board: The board to read.
            origin: Square of the pawn.

        Returns:
            Up to one single step, one double step, and two captures.
        """
        piece = board.require_piece_at(origin)
        moves: list[Move] = []
        forward = Offset(piece.color.forward, 0)

        one_ahead = origin.shifted(forward)
        if one_ahead is not None and board.is_empty(one_ahead):
            moves.append(Move.simple(origin, one_ahead, capture=False))

            # Nested, so the double step cannot jump a blocked first square.
            if not piece.has_moved:
                far = origin.shifted(forward, self.double_step_distance)
                if far is not None and board.is_empty(far):
                    moves.append(Move.simple(origin, far, capture=False))

        for sideways in (-1, 1):
            target = origin.shifted(Offset(piece.color.forward, sideways))
            if target is None:
                continue
            if board.capturable_enemy_at(target, piece.color) is not None:
                moves.append(Move.simple(origin, target, capture=True))

        return tuple(moves)

    @property
    def description(self) -> str:
        """
        Summarise this rule in plain language.

        Returns:
            A fixed description of pawn movement.
        """
        return "moves forward, captures diagonally forward"


@dataclass(frozen=True, slots=True)
class NoMovementRule(MovementRule):
    """
    A piece that cannot move or capture, such as the Time Machine.

    An explicit rule rather than an empty override, so immobility is a stated
    property a test can assert and the registry needs no special case.

    Attributes:
        reason: Why this piece cannot move, shown in variant metadata.
    """

    reason: str = "cannot move or capture"

    def candidates(self, board: Board, origin: Coordinate) -> tuple[Move, ...]:
        """
        List no moves, after confirming a piece is present.

        Arguments:
            board: The board to read.
            origin: Square of the immobile piece.

        Returns:
            An empty tuple.
        """
        board.require_piece_at(origin)
        return ()

    @property
    def description(self) -> str:
        """
        Summarise this rule in plain language.

        Returns:
            The configured reason the piece cannot move.
        """
        return self.reason


@dataclass(frozen=True, slots=True)
class CompositeRule(MovementRule):
    """
    Several rules at once, for pieces that combine mechanisms.

    The Grand Empress is a knight leap plus a queen slide. Under method
    inheritance she would have to pick one parent; here she holds both rules.

    Attributes:
        rules: The component rules, applied in order.
    """

    rules: tuple[MovementRule, ...]

    def candidates(self, board: Board, origin: Coordinate) -> tuple[Move, ...]:
        """
        List the union of every component rule's moves.

        Arguments:
            board: The board to read.
            origin: Square of the piece.

        Returns:
            Candidate moves with duplicates removed, since two component rules
            can reach the same square by different routes. Empty when this rule
            has no components, which still requires a piece on the origin.
        """
        board.require_piece_at(origin)

        seen: dict[tuple[Coordinate, Coordinate, object], Move] = {}
        for rule in self.rules:
            for move in rule.candidates(board, origin):
                seen.setdefault((move.origin, move.destination, move.action), move)
        return tuple(seen.values())

    @property
    def description(self) -> str:
        """
        Summarise this rule in plain language.

        Returns:
            The component descriptions joined together.
        """
        return " and ".join(rule.description for rule in self.rules)


def step_rule(offsets: tuple[Offset, ...], *, can_capture: bool = True) -> LeapRule:
    """
    Build a leap rule over adjacent squares.

    A named constructor so the call site can say "step" where that is the
    intent, without a second class that behaves identically.

    Arguments:
        offsets: Adjacent directions the piece may step to.
        can_capture: Whether stepping onto an enemy removes it.

    Returns:
        A LeapRule configured for single-square movement.
    """
    return LeapRule(offsets=offsets, can_capture=can_capture)
