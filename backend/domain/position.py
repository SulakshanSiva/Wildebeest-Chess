from __future__ import annotations

from dataclasses import dataclass, replace

from .board import Board
from .coordinates import Coordinate
from .enums import Color, PieceKind

# Which pieces stand where, and whose turn it is: what makes two positions the same.
RepetitionKey = tuple[Color, tuple[tuple[Coordinate, PieceKind, Color], ...]]


@dataclass(frozen=True, slots=True)
class Position:
    """
    A complete snapshot of play: the board plus whose turn it is.

    Separate from Board because "whose turn" is not a property of the grid, and
    separate from Game because a position carries no history, status or
    version. That makes it the right unit for AI search, which explores
    hypothetical positions that are not games.

    Attributes:
        board: The pieces and terrain.
        side_to_move: Which colour moves next.
        ply: How many moves have been played to reach this position.
    """

    board: Board
    side_to_move: Color
    ply: int = 0

    def with_board(self, board: Board) -> Position:
        """
        Give a copy of this position holding a different board.

        The side to move is unchanged, so an applier can swap the board and
        hand over the turn as two explicit steps.

        Arguments:
            board: The replacement board.

        Returns:
            A new position.
        """
        return replace(self, board=board)

    def with_turn_passed(self) -> Position:
        """
        Give a copy with the turn handed to the opponent.

        Returns:
            A new position with the side to move flipped and the ply advanced.
        """
        return replace(self, side_to_move=self.side_to_move.opponent, ply=self.ply + 1)

    @property
    def repetition_key(self) -> RepetitionKey:
        """
        Identify this position for spotting repetitions.

        Two positions repeat when the same kinds and colours stand on the same
        squares with the same side to move. Piece ids and first-move flags are
        left out, so a piece that walks away and back makes the same key.

        Returns:
            A hashable key, equal for repeated positions.
        """
        pieces = tuple((square, piece.kind, piece.color) for square, piece in self.board.pieces())
        return (self.side_to_move, pieces)

    def __str__(self) -> str:
        """
        Render the position for test failures and debugging.

        Returns:
            The side to move followed by the board as layout characters.
        """
        return f"{self.side_to_move.value} to move\n{self.board}"
