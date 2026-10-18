from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count

from .board import Board, Cell
from .coordinates import Coordinate
from .enums import Color, Terrain
from .errors import BoardSetupError
from .pieces.registry import create_piece, kind_for_symbol
from .position import Position
from .rules.terrain import TransporterLinks, validate_links

# Uppercase is White on rows 0-1; lowercase is Black on rows 9-10.
WILDEBEEST_LAYOUT = """
RNZBOKXBCNR
GPPSPJPPPPG
...........
.*.......*.
...........
.....#.....
...........
.*.......*.
...........
gppspjppppg
rnzbokxbcnr
"""

_TERRAIN_SYMBOLS: dict[str, Terrain] = {terrain.symbol: terrain for terrain in Terrain}

# Where each transporter pad sends its occupant. A single four-cycle:
# (3,1) -> (7,9) -> (7,1) -> (3,9) -> (3,1). Because it is a permutation of the
# pad squares, every occupant can move at once without two landing together.
WILDEBEEST_TRANSPORTER_LINKS: TransporterLinks = {
    Coordinate(3, 9): Coordinate(3, 1),
    Coordinate(7, 1): Coordinate(3, 9),
    Coordinate(7, 9): Coordinate(7, 1),
    Coordinate(3, 1): Coordinate(7, 9),
}


@dataclass(frozen=True, slots=True)
class Variant:
    """
    A named ruleset and the starting position it produces.

    Parsing a layout is a configuration concern, so it lives here rather than
    in Board or in movement code. That keeps any layout loadable for a test.

    Attributes:
        variant_id: Stable identifier used by the API.
        name: Human-readable name.
        layout: The starting layout as text.
        first_player: Which side moves first.
        transporter_links: Where each transporter pad sends its occupant.
    """

    variant_id: str = "wildebeest"
    name: str = "Wildebeest Chess"
    layout: str = WILDEBEEST_LAYOUT
    first_player: Color = Color.WHITE
    transporter_links: TransporterLinks = field(
        default_factory=lambda: dict(WILDEBEEST_TRANSPORTER_LINKS)
    )

    def build_board(self) -> Board:
        """
        Parse this variant's layout into a board.

        Returns:
            A validated board with terrain and pieces placed, whose transporter
            pads match this variant's links.
        """
        board = parse_layout(self.layout)
        validate_links(board, self.transporter_links)
        return board

    def initial_position(self) -> Position:
        """
        Build the position a new game starts from.

        Returns:
            A position holding the starting board and the first player to move.
        """
        return Position(board=self.build_board(), side_to_move=self.first_player)


def parse_layout(layout: str, *, first_piece_id: int = 1) -> Board:
    """
    Turn a text layout into a board of cells.

    Terrain and occupancy are recorded separately, so a piece standing on a
    special square does not erase it.

    Arguments:
        layout: Rows of layout characters, one line per board row. Leading and
            trailing blank lines are ignored.
        first_piece_id: Identity to assign the first piece found.

    Returns:
        A validated board.
    """
    lines = layout.strip().splitlines()
    if not lines:
        raise BoardSetupError("layout is empty")

    widths = {len(line) for line in lines}
    if len(widths) != 1:
        raise BoardSetupError(f"layout rows have inconsistent widths: {sorted(widths)}")

    ids = count(first_piece_id)
    rows: list[tuple[Cell, ...]] = []

    for row_index, line in enumerate(lines):
        cells: list[Cell] = []
        for column, character in enumerate(line):
            cells.append(_parse_cell(character, row_index, column, ids))
        rows.append(tuple(cells))

    board = Board.from_cells(tuple(rows))
    board.validate()
    return board


def _parse_cell(character: str, row: int, column: int, ids: count[int]) -> Cell:
    """
    Decode one layout character into a cell.

    Arguments:
        character: The layout character to decode.
        row: Row the character came from, for error messages.
        column: Column the character came from, for error messages.
        ids: Counter supplying the next piece identity.

    Returns:
        A cell holding either terrain alone or terrain plus a piece.
    """
    terrain = _TERRAIN_SYMBOLS.get(character)
    if terrain is not None:
        return Cell(terrain=terrain)

    # Pieces always start on normal squares; the layout cannot express a piece
    # standing on special terrain, which needs revisiting once "#" and "*" mean
    # something.
    kind, color = kind_for_symbol(character, row, column)
    piece = create_piece(piece_id=next(ids), kind=kind, color=color)
    return Cell(terrain=Terrain.NORMAL, piece=piece)
