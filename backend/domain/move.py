from __future__ import annotations

from dataclasses import dataclass, field

from .coordinates import Coordinate
from .enums import Color, MoveAction, PieceKind, RemovalCause


@dataclass(frozen=True, slots=True)
class Displacement:
    """
    A piece shoved between squares as a side effect of another piece's move.

    Only the Gorilla produces one today: it steps onto an occupied square and
    the occupant is pushed one square further along the same direction.

    Attributes:
        origin: Where the shoved piece started.
        destination: Where it ends up.
    """

    origin: Coordinate
    destination: Coordinate


@dataclass(frozen=True, slots=True)
class Transport:
    """
    A piece carried between transporter pads during the after-effects.

    Attributes:
        piece_id: Identity of the piece that was carried.
        kind: Its kind when it was carried.
        origin: The pad it left.
        destination: The pad it arrived on.
    """

    piece_id: int
    kind: PieceKind
    origin: Coordinate
    destination: Coordinate


@dataclass(frozen=True, slots=True)
class Move:
    """
    One candidate change to the board.

    Three squares rather than two is what makes the Catapult expressible. For
    most moves actor and origin are the same square:

    MOVE and CAPTURE have the mover at actor and origin, with destination empty
    or holding an enemy. PUSH adds a displaced occupant. FLING puts the
    catapult at actor and the launched piece at origin, because the piece that
    moves is not the piece whose turn it is and the catapult stays put. That
    last case is why a move needs three squares rather than two.

    Attributes:
        actor: Square of the piece whose turn this move spends.
        origin: Square of the piece that is actually displaced.
        destination: Where the displaced piece ends up.
        action: How the applier should resolve the move.
        displaced: A secondary shove, used by PUSH.
    """

    actor: Coordinate
    origin: Coordinate
    destination: Coordinate
    action: MoveAction
    displaced: Displacement | None = None

    @classmethod
    def simple(cls, origin: Coordinate, destination: Coordinate, *, capture: bool) -> Move:
        """
        Build a move where the piece that moves is the piece spending the turn.

        Arguments:
            origin: Square the piece starts on.
            destination: Square it moves to.
            capture: Whether an enemy occupies the destination.

        Returns:
            A move with action CAPTURE or MOVE.
        """
        return cls(
            actor=origin,
            origin=origin,
            destination=destination,
            action=MoveAction.CAPTURE if capture else MoveAction.MOVE,
        )

    @classmethod
    def push(cls, origin: Coordinate, destination: Coordinate, push_to: Coordinate) -> Move:
        """
        Build a Gorilla step that shoves the occupant of the destination onward.

        Arguments:
            origin: Square the gorilla starts on.
            destination: Occupied square it steps onto.
            push_to: Square the occupant is shoved to.

        Returns:
            A move with action PUSH and a displacement recorded.
        """
        return cls(
            actor=origin,
            origin=origin,
            destination=destination,
            action=MoveAction.PUSH,
            displaced=Displacement(origin=destination, destination=push_to),
        )

    @classmethod
    def crush(cls, origin: Coordinate, destination: Coordinate) -> Move:
        """
        Build a Gorilla step that destroys the occupant it cannot push onward.

        Used when the pushed piece has nowhere to go: the square beyond it is
        occupied. The occupant is removed and the Gorilla takes its square.

        Arguments:
            origin: Square the gorilla starts on.
            destination: Occupied square it steps onto.

        Returns:
            A move with action CRUSH and no displacement.
        """
        return cls(
            actor=origin,
            origin=origin,
            destination=destination,
            action=MoveAction.CRUSH,
        )

    @classmethod
    def fling(cls, catapult: Coordinate, passenger: Coordinate, landing: Coordinate) -> Move:
        """
        Build a Catapult launch, in which the catapult itself does not move.

        Arguments:
            catapult: Square of the catapult spending the turn.
            passenger: Square of the adjacent piece being launched.
            landing: Square the launched piece arrives on.

        Returns:
            A move with action FLING.
        """
        return cls(
            actor=catapult,
            origin=passenger,
            destination=landing,
            action=MoveAction.FLING,
        )

    @property
    def is_actor_moving(self) -> bool:
        """
        Say whether the piece spending the turn is the piece that moves.

        Returns:
            False for a fling, True otherwise.
        """
        return self.actor == self.origin

    def __str__(self) -> str:
        """
        Render the move for logs and test output.

        Returns:
            The action, the squares, and the actor when it differs.
        """
        arrow = f"{self.origin}->{self.destination}"
        if self.is_actor_moving:
            return f"{self.action.name} {arrow}"
        return f"{self.action.name} by {self.actor} {arrow}"


@dataclass(frozen=True, slots=True)
class MoveRecord:
    """
    A move that was actually applied, together with everything it caused.

    The move alone cannot be replayed or undone, because a capture has to
    remember what it removed. Pieces are stored as ids and kinds rather than
    live objects so a record stays valid as the board moves on. The removed and
    promoted pieces cover the whole turn, after-effects included, since poison,
    a rampage or an explosion can change the board long after the move itself.

    Attributes:
        move: The move that was applied.
        moved_piece_id: Identity of the piece that spent the turn.
        side: The colour that made the move.
        moved: Id and kind of the piece that travelled from origin to
            destination. The same as the actor except for a fling, where it is
            the passenger.
        displaced: Id and kind of the piece a Gorilla pushed, if any.
        captured: Id and kind of each piece removed during the turn.
        causes: Why each captured piece was removed, by id.
        promoted: Id and new kind of each piece that changed kind.
        transported: Every piece a transporter pad carried this turn.
        ply: Zero-based index of this move in the game.
    """

    move: Move
    moved_piece_id: int
    side: Color
    moved: tuple[int, PieceKind]
    displaced: tuple[int, PieceKind] | None = None
    captured: tuple[tuple[int, PieceKind], ...] = field(default_factory=tuple)
    causes: tuple[tuple[int, RemovalCause], ...] = field(default_factory=tuple)
    promoted: tuple[tuple[int, PieceKind], ...] = field(default_factory=tuple)
    transported: tuple[Transport, ...] = field(default_factory=tuple)
    ply: int = 0
