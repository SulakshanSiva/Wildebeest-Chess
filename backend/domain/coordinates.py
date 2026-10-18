from __future__ import annotations

from dataclasses import dataclass

from .errors import InvalidCoordinateError


@dataclass(frozen=True, slots=True)
class Offset:
    """
    A direction or step vector in board space.

    Separate from Coordinate because a coordinate names a square that must
    exist, while an offset is free to point off the board, which is how a slide
    discovers its own edge.

    Attributes:
        d_row: Change in row.
        d_column: Change in column.
    """

    d_row: int
    d_column: int

    @property
    def inverted(self) -> Offset:
        """
        Give the same direction reversed.

        Used by the Catapult, which flings a neighbour away from itself.

        Returns:
            An offset with both components negated.
        """
        return Offset(-self.d_row, -self.d_column)

    @property
    def is_adjacent_step(self) -> bool:
        """
        Say whether this offset reaches a touching square.

        Uses Chebyshev distance, so a diagonal step counts as adjacent.

        Returns:
            True when neither component exceeds one square.
        """
        return max(abs(self.d_row), abs(self.d_column)) <= 1


@dataclass(frozen=True, slots=True)
class Coordinate:
    """
    A square address, validated at construction.

    Bounds are deliberately not checked here. Whether a square exists belongs
    to the board, because a 3x3 test fixture and the 11x11 game board disagree
    about what is in bounds, and piece rules must be testable against both. So
    this validates shape and Board.contains validates membership.

    Attributes:
        row: Zero-based row index.
        column: Zero-based column index.
    """

    row: int
    column: int

    def __post_init__(self) -> None:
        """
        Reject values that cannot name a square.

        bool is a subclass of int, so an exact type check keeps Coordinate(True,
        0) from being read as the top-left corner.
        """
        if (
            type(self.row) is not int
            or type(self.column) is not int
            or self.row < 0
            or self.column < 0
        ):
            raise InvalidCoordinateError(self.row, self.column)

    def shifted(self, offset: Offset, times: int = 1) -> Coordinate | None:
        """
        Give this square moved by an offset.

        Returns None rather than raising, because walking off the edge is how a
        slide normally terminates and not an error.

        Arguments:
            offset: Direction to move in.
            times: How many times to apply the offset.

        Returns:
            The resulting square, or None if it would leave the grid.
        """
        row = self.row + offset.d_row * times
        column = self.column + offset.d_column * times
        if row < 0 or column < 0:
            return None
        return Coordinate(row, column)

    def __str__(self) -> str:
        """
        Render the square for logs and test output.

        Returns:
            The coordinate as "(row, column)".
        """
        return f"({self.row}, {self.column})"


# Declared once, so a correction reaches every piece that uses them.
ORTHOGONAL: tuple[Offset, ...] = (
    Offset(1, 0),
    Offset(-1, 0),
    Offset(0, 1),
    Offset(0, -1),
)

DIAGONAL: tuple[Offset, ...] = (
    Offset(1, 1),
    Offset(1, -1),
    Offset(-1, 1),
    Offset(-1, -1),
)

ALL_DIRECTIONS: tuple[Offset, ...] = ORTHOGONAL + DIAGONAL

KNIGHT_LEAPS: tuple[Offset, ...] = (
    Offset(2, 1),
    Offset(2, -1),
    Offset(-2, 1),
    Offset(-2, -1),
    Offset(1, 2),
    Offset(1, -2),
    Offset(-1, 2),
    Offset(-1, -2),
)

# The Golf Cart's only directions: one square along its own row.
SIDEWAYS: tuple[Offset, ...] = (Offset(0, 1), Offset(0, -1))
