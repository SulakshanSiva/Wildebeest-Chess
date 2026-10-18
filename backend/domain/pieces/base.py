from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from ..coordinates import Coordinate
from ..enums import Color, PieceKind

if TYPE_CHECKING:
    # Type hints only. Board holds Piece at runtime, so a runtime import of
    # Board here would be circular.
    from ..board import Board
    from ..move import Move


class MovementRule(ABC):
    """
    How one piece generates candidate moves.

    Implementations must be pure: read the board, return moves, change nothing.
    Asking what a piece could do must never alter the game.

    The contract takes the board and an origin square rather than a piece, so a
    caller cannot pass a piece that is not actually standing there.
    """

    @abstractmethod
    def candidates(self, board: Board, origin: Coordinate) -> tuple[Move, ...]:
        """
        List every move the piece on a square could geometrically make.

        These are candidates: valid for occupancy and terrain. The move
        generator adds turn order and paralysis to make them legal; there is no
        king safety to check, since the rules have no check.

        Arguments:
            board: The board to read. Never modified.
            origin: Square of the piece whose moves are wanted.

        Returns:
            A tuple of candidate moves, empty if the piece cannot move.
        """

    @property
    def description(self) -> str:
        """
        Summarise this rule in plain language.

        Feeds the variant metadata endpoint so the front end does not hard-code
        rule text.

        Returns:
            A short human-readable description.
        """
        return type(self).__name__


@dataclass(frozen=True, slots=True)
class Piece:
    """
    A piece on the board.

    A piece holds no square and no board. The board already maps square to
    piece, so storing position here would let the two disagree, and a piece
    that holds its board can mutate shared state during move generation and
    cannot be tested on its own. Dimensions belong to the board, and the
    opposing colour is derivable from color.

    Attributes:
        piece_id: Stable identity, so an effect can name which piece it
            displaced even after the board has changed.
        kind: What type of piece this is.
        color: Which side owns it.
        movement: The rule that generates its candidate moves.
        has_moved: Whether it has moved yet, which the pawn's double step reads.
    """

    piece_id: int
    kind: PieceKind
    color: Color
    movement: MovementRule
    has_moved: bool = False

    def moved(self) -> Piece:
        """
        Give this piece marked as having moved.

        Returns a new piece rather than mutating, because positions are shared
        between AI search branches.

        Returns:
            A piece with has_moved set, or self if it was already set.
        """
        return self if self.has_moved else replace(self, has_moved=True)

    def __str__(self) -> str:
        """
        Render the piece for logs and test output.

        Returns:
            A short identifier such as "w:rook#3".
        """
        return f"{self.color.value[0]}:{self.kind.value}#{self.piece_id}"
