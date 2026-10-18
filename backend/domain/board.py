from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .coordinates import Coordinate
from .enums import Color, Terrain
from .errors import (
    BoardSetupError,
    InvariantViolation,
    OutOfBoundsError,
    SquareEmptyError,
    SquareOccupiedError,
)
from .pieces.base import Piece
from .pieces.registry import symbol_for


@dataclass(frozen=True, slots=True)
class BoardDimensions:
    """
    How big a board is.

    A value object rather than two integers on Board, so bounds checking has
    one home and test fixtures can be small. Piece rules must be verifiable
    against several board sizes, which is only possible if 11x11 is data rather
    than a constant compiled into the rules.

    Attributes:
        rows: Number of rows.
        columns: Number of columns.
    """

    rows: int
    columns: int

    def __post_init__(self) -> None:
        """
        Reject degenerate board sizes.
        """
        if self.rows < 1 or self.columns < 1:
            raise BoardSetupError(f"board must be at least 1x1, got {self.rows}x{self.columns}")

    def contains(self, square: Coordinate) -> bool:
        """
        Say whether a square exists on a board of this size.

        Arguments:
            square: The square to test. Already known to be non-negative.

        Returns:
            True when both indices are within the dimensions.
        """
        return square.row < self.rows and square.column < self.columns

    def require_contains(self, square: Coordinate) -> None:
        """
        Assert that a square exists on a board of this size.

        Arguments:
            square: The square to check.
        """
        if not self.contains(square):
            raise OutOfBoundsError(square.row, square.column, self.rows, self.columns)

    def squares(self) -> Iterator[Coordinate]:
        """
        Walk every square, row by row.

        Returns:
            An iterator over all coordinates in reading order.
        """
        for row in range(self.rows):
            for column in range(self.columns):
                yield Coordinate(row, column)


@dataclass(frozen=True, slots=True)
class Cell:
    """
    One square: what it is, and what stands on it.

    Terrain and occupancy are independent fields, so a piece can stand on a
    special square without erasing it.

    Attributes:
        terrain: What kind of square this is.
        piece: The occupant, or None.
    """

    terrain: Terrain = Terrain.NORMAL
    piece: Piece | None = None

    @property
    def is_empty(self) -> bool:
        """
        Say whether the square is unoccupied.

        Returns:
            True when no piece stands here.
        """
        return self.piece is None

    @property
    def is_occupied(self) -> bool:
        """
        Say whether a piece stands here.

        Returns:
            True when the square holds a piece.
        """
        return self.piece is not None


@dataclass(frozen=True, slots=True)
class Board:
    """
    An immutable grid of cells.

    Every mutator returns a new board, so applying a move never changes its
    source position. That is what makes AI search branches independent and
    replay reliable. An 11x11 board is 121 cells, so a copy is cheap; a mutable
    optimisation later must keep this interface and pass the same tests.

    Build with empty or from_cells rather than by hand.

    Attributes:
        dimensions: The board's size.
        cells: Rows of cells, outermost index first.
    """

    dimensions: BoardDimensions
    cells: tuple[tuple[Cell, ...], ...]

    @classmethod
    def empty(cls, dimensions: BoardDimensions) -> Board:
        """
        Build a board of normal, unoccupied squares.

        Arguments:
            dimensions: Size of the board to build.

        Returns:
            A board with every cell empty and normal terrain.
        """
        row = tuple(Cell() for _ in range(dimensions.columns))
        return cls(dimensions=dimensions, cells=tuple(row for _ in range(dimensions.rows)))

    @classmethod
    def from_cells(cls, cells: tuple[tuple[Cell, ...], ...]) -> Board:
        """
        Build a board from a complete grid, validating that it is rectangular.

        Arguments:
            cells: Rows of cells, all of equal length.

        Returns:
            A board whose dimensions are inferred from the grid.
        """
        if not cells or not cells[0]:
            raise BoardSetupError("board must have at least one cell")
        columns = len(cells[0])
        if any(len(row) != columns for row in cells):
            widths = sorted({len(row) for row in cells})
            raise BoardSetupError(f"board rows have inconsistent widths: {widths}")
        return cls(dimensions=BoardDimensions(len(cells), columns), cells=cells)

    @property
    def rows(self) -> int:
        """
        Give the number of rows.

        Returns:
            The board's row count.
        """
        return self.dimensions.rows

    @property
    def columns(self) -> int:
        """
        Give the number of columns.

        Returns:
            The board's column count.
        """
        return self.dimensions.columns

    def contains(self, square: Coordinate) -> bool:
        """
        Say whether a square exists on this board.

        Arguments:
            square: The square to test.

        Returns:
            True when the square is in bounds.
        """
        return self.dimensions.contains(square)

    def cell_at(self, square: Coordinate) -> Cell:
        """
        Give the cell on a square.

        Arguments:
            square: The square to read. Must be in bounds.

        Returns:
            The cell, including its terrain and any occupant.
        """
        self.dimensions.require_contains(square)
        return self.cells[square.row][square.column]

    def piece_at(self, square: Coordinate) -> Piece | None:
        """
        Give the piece on a square, if any.

        None means empty, which is a real answer rather than a failure.

        Arguments:
            square: The square to read. Must be in bounds.

        Returns:
            The occupying piece, or None when the square is empty.
        """
        return self.cell_at(square).piece

    def require_piece_at(self, square: Coordinate) -> Piece:
        """
        Give the piece on a square, raising if there is none.

        For callers that have already established a piece must be there, so a
        missing one is a defect rather than a branch to handle.

        Arguments:
            square: The square to read.

        Returns:
            The occupying piece.
        """
        piece = self.piece_at(square)
        if piece is None:
            raise SquareEmptyError(square.row, square.column)
        return piece

    def is_empty(self, square: Coordinate) -> bool:
        """
        Say whether a piece may move onto a square.

        Requires in bounds, unoccupied, and passable terrain. Every terrain is
        passable: the jet pack and transporter pads act on a piece that lands on
        them rather than blocking it.

        Arguments:
            square: The square to test. May be out of bounds.

        Returns:
            True when the square can receive a piece.
        """
        if not self.contains(square):
            return False
        cell = self.cell_at(square)
        return cell.is_empty and cell.terrain.is_passable

    def enemy_at(self, square: Coordinate, color: Color) -> Piece | None:
        """
        Give the piece on a square if it opposes a colour.

        Arguments:
            square: The square to test. May be out of bounds.
            color: The colour the occupant must oppose.

        Returns:
            The enemy piece, or None when the square is off the board, empty,
            or holds a friendly piece.
        """
        if not self.contains(square):
            return None
        piece = self.piece_at(square)
        if piece is not None and piece.color is not color:
            return piece
        return None

    def pieces(self, color: Color | None = None) -> Iterator[tuple[Coordinate, Piece]]:
        """
        Walk every occupied square.

        Arguments:
            color: Restrict to one side, or None for both.

        Returns:
            An iterator of square and piece pairs, in reading order.
        """
        for square in self.dimensions.squares():
            piece = self.cells[square.row][square.column].piece
            if piece is not None and (color is None or piece.color is color):
                yield square, piece

    def _replaced(self, changes: dict[Coordinate, Cell]) -> Board:
        """
        Give a copy of this board with specific cells swapped out.

        Rebuilds only the affected rows. Untouched rows are shared, since every
        cell is immutable and safe to alias.

        Arguments:
            changes: New cell for each square being changed.

        Returns:
            A new board of the same dimensions.
        """
        touched_rows = {square.row for square in changes}
        new_cells: list[tuple[Cell, ...]] = []

        for row_index, row in enumerate(self.cells):
            if row_index not in touched_rows:
                new_cells.append(row)
                continue
            rebuilt = tuple(
                changes.get(Coordinate(row_index, column), cell) for column, cell in enumerate(row)
            )
            new_cells.append(rebuilt)

        return Board(dimensions=self.dimensions, cells=tuple(new_cells))

    def with_piece(self, square: Coordinate, piece: Piece) -> Board:
        """
        Give a copy with a piece placed on an empty square.

        Arguments:
            square: Where to place the piece.
            piece: The piece to place.

        Returns:
            A new board with the square occupied and its terrain preserved.
        """
        cell = self.cell_at(square)
        if cell.is_occupied:
            raise SquareOccupiedError(square.row, square.column)
        return self._replaced({square: Cell(terrain=cell.terrain, piece=piece)})

    def without_piece(self, square: Coordinate) -> Board:
        """
        Give a copy with a square cleared.

        Arguments:
            square: The square to clear. Must be occupied.

        Returns:
            A new board with the square empty and its terrain preserved.
        """
        cell = self.cell_at(square)
        if cell.is_empty:
            raise SquareEmptyError(square.row, square.column)
        return self._replaced({square: Cell(terrain=cell.terrain, piece=None)})

    def with_piece_relocated(
        self, origin: Coordinate, destination: Coordinate, *, mark_moved: bool = True
    ) -> Board:
        """
        Give a copy with a piece moved between squares.

        The destination must be empty. Captures remove the occupant first, in
        the move applier, so a capture is never implicit in a relocation.

        Arguments:
            origin: Square the piece leaves. Must be occupied.
            destination: Square it arrives on. Must be empty.
            mark_moved: Whether the piece counts as having moved. False for a piece
                that was shoved or flung, since it did not spend its own turn.

        Returns:
            A new board with the piece relocated and marked as having moved.
        """
        origin_cell = self.cell_at(origin)
        destination_cell = self.cell_at(destination)

        piece = origin_cell.piece
        if piece is None:
            raise SquareEmptyError(origin.row, origin.column)
        if destination_cell.is_occupied:
            raise SquareOccupiedError(destination.row, destination.column)

        return self._replaced(
            {
                origin: Cell(terrain=origin_cell.terrain, piece=None),
                destination: Cell(
                    terrain=destination_cell.terrain,
                    piece=piece.moved() if mark_moved else piece,
                ),
            }
        )

    def validate(self) -> None:
        """
        Assert this board's structural invariants.

        Called after setup and after each applied move in tests. A failure is a
        defect in the engine rather than bad input.
        """
        if len(self.cells) != self.rows:
            raise InvariantViolation(f"expected {self.rows} rows, found {len(self.cells)}")

        seen_ids: dict[int, Coordinate] = {}
        for row_index, row in enumerate(self.cells):
            if len(row) != self.columns:
                raise InvariantViolation(
                    f"row {row_index} has {len(row)} cells, expected {self.columns}"
                )
            for column, cell in enumerate(row):
                piece = cell.piece
                if piece is None:
                    continue
                if piece.piece_id in seen_ids:
                    raise InvariantViolation(
                        f"piece id {piece.piece_id} appears at "
                        f"{seen_ids[piece.piece_id]} and ({row_index}, {column})"
                    )
                seen_ids[piece.piece_id] = Coordinate(row_index, column)

    def __str__(self) -> str:
        """
        Render the board as layout characters.

        For test failures and debugging only. This is not a serialisation
        format; the wire format is a schema at the API boundary.

        Returns:
            One line per row, using terrain and piece symbols.
        """
        lines = []
        for row in self.cells:
            lines.append(
                "".join(
                    cell.terrain.symbol if cell.piece is None else symbol_for(cell.piece)
                    for cell in row
                )
            )
        return "\n".join(lines)
