from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..coordinates import ALL_DIRECTIONS, Coordinate, Offset
from ..enums import PieceKind
from ..move import Move
from .base import MovementRule

if TYPE_CHECKING:
    from ..board import Board


@dataclass(frozen=True, slots=True)
class PushRule(MovementRule):
    """
    The Gorilla's movement: step like a King, shoving whatever is in the way.

    The Gorilla never captures by moving onto a piece. Stepping onto an
    occupied square pushes the occupant one further in the same direction. If
    that square is blocked the occupant is crushed instead, which is the only
    way a Gorilla removes a piece.

    Attributes:
        directions: The squares the Gorilla may step to.
    """

    directions: tuple[Offset, ...] = ALL_DIRECTIONS

    def candidates(self, board: Board, origin: Coordinate) -> tuple[Move, ...]:
        """
        List the Gorilla's steps, pushes and crushes.

        Arguments:
            board: The board to read.
            origin: Square of the Gorilla.

        Returns:
            One move per direction that resolves, and none for directions that
            are blocked by a Gorilla, a hovering piece, or the board edge.
        """
        board.require_piece_at(origin)
        moves: list[Move] = []

        for direction in self.directions:
            destination = origin.shifted(direction)
            if destination is None or not board.contains(destination):
                continue

            if board.is_empty(destination):
                moves.append(Move.simple(origin, destination, capture=False))
                continue

            occupant = board.require_piece_at(destination)
            # A Gorilla cannot be pushed, and a hovering piece floats clear.
            if occupant.kind is PieceKind.GORILLA or occupant.kind.is_hovering:
                continue

            push_to = destination.shifted(direction)
            # The Gorilla may not push a piece off the board at all.
            if push_to is None or not board.contains(push_to):
                continue

            if board.is_empty(push_to):
                moves.append(Move.push(origin, destination, push_to))
                continue

            # Blocked: the pushed piece is crushed, unless a Gorilla blocks it.
            blocker = board.require_piece_at(push_to)
            if blocker.kind is not PieceKind.GORILLA:
                moves.append(Move.crush(origin, destination))

        return tuple(moves)

    @property
    def description(self) -> str:
        """
        Summarise this rule in plain language.

        Returns:
            A fixed description of the Gorilla's movement.
        """
        return "steps one square, pushing or crushing the occupant; never captures"


@dataclass(frozen=True, slots=True)
class FlingRule(MovementRule):
    """
    The Catapult's turn: step like a King, or launch a friendly neighbour.

    The Catapult cannot capture by moving. Flinging spends its turn and the
    Catapult itself does not move, which is why a flung move names the Catapult
    as actor and the passenger as origin.

    A flung piece travels in the direction running from itself through the
    Catapult, so it passes over the Catapult and lands beyond. It flies over
    every piece in its path and may land on any empty square, or capture an
    enemy that is neither royal nor a Gorilla.

    Being flung does not consume the passenger's first move: the Catapult spent
    the turn, not the passenger. The move applier places it unmarked.

    Attributes:
        directions: The squares the Catapult may step to and fling from.
    """

    directions: tuple[Offset, ...] = ALL_DIRECTIONS

    def candidates(self, board: Board, origin: Coordinate) -> tuple[Move, ...]:
        """
        List the Catapult's own steps and every fling it can perform.

        Arguments:
            board: The board to read.
            origin: Square of the Catapult.

        Returns:
            Steps onto empty squares, plus one move per reachable landing
            square for each friendly neighbour it can launch.
        """
        catapult = board.require_piece_at(origin)
        moves: list[Move] = []

        for direction in self.directions:
            neighbour = origin.shifted(direction)
            if neighbour is None or not board.contains(neighbour):
                continue

            # The Catapult moves like a King but cannot capture.
            if board.is_empty(neighbour):
                moves.append(Move.simple(origin, neighbour, capture=False))
                continue

            passenger = board.require_piece_at(neighbour)
            if passenger.color is not catapult.color:
                continue
            if passenger.kind is PieceKind.TIME_MACHINE:
                continue

            # The passenger travels from itself through the Catapult, which is
            # the reverse of the direction that found it.
            moves.extend(self._landings(board, origin, neighbour, direction.inverted))

        return tuple(moves)

    def _landings(
        self,
        board: Board,
        catapult: Coordinate,
        passenger: Coordinate,
        direction: Offset,
    ) -> list[Move]:
        """
        List every square a launched neighbour can reach along its ray.

        The ray runs from the passenger through the Catapult and onward, so it
        starts one square past the Catapult. A flung piece flies over whatever
        it passes, so a blocked square ends nothing.

        Arguments:
            board: The board to read.
            catapult: Square of the Catapult doing the flinging.
            passenger: Square of the piece being launched.
            direction: Offset running from the passenger to the Catapult.

        Returns:
            A fling move per landing square, empty or capturable.
        """
        moves: list[Move] = []
        colour = board.require_piece_at(passenger).color
        landing = catapult.shifted(direction)

        while landing is not None and board.contains(landing):
            if board.is_empty(landing):
                moves.append(Move.fling(catapult, passenger, landing))
            else:
                target = board.require_piece_at(landing)
                # A flung piece may never take a King or a Gorilla.
                if (
                    target.color is not colour
                    and not target.kind.is_royal
                    and target.kind is not PieceKind.GORILLA
                ):
                    moves.append(Move.fling(catapult, passenger, landing))
            landing = landing.shifted(direction)

        return moves

    @property
    def description(self) -> str:
        """
        Summarise this rule in plain language.

        Returns:
            A fixed description of the Catapult's movement and fling.
        """
        return "steps one square without capturing, or flings a friendly neighbour past itself"


@dataclass(frozen=True, slots=True)
class EdgeRowsOnlyRule(MovementRule):
    """
    A rule that applies only on the top and bottom rows of the board.

    The Golf Cart moves and captures left and right in the bottom and top rows
    only. It normally cannot leave them, but a Gorilla push or a Catapult fling
    can displace one, and a displaced cart is immobile until something returns
    it to an edge row.

    Attributes:
        inner: The rule to apply while on an edge row.
    """

    inner: MovementRule

    def candidates(self, board: Board, origin: Coordinate) -> tuple[Move, ...]:
        """
        Delegate to the inner rule, but only from the top or bottom row.

        Arguments:
            board: The board to read.
            origin: Square of the piece.

        Returns:
            The inner rule's moves on an edge row, nothing anywhere else.
        """
        board.require_piece_at(origin)
        if origin.row not in (0, board.rows - 1):
            return ()
        return self.inner.candidates(board, origin)

    @property
    def description(self) -> str:
        """
        Summarise this rule in plain language.

        Returns:
            The inner description, qualified by the row restriction.
        """
        return f"{self.inner.description}, and only on the top and bottom rows"
