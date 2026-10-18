from collections.abc import Callable

import pytest

from backend.domain.board import Board, BoardDimensions, Cell
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, PieceKind, Terrain
from backend.domain.errors import (
    BoardSetupError,
    InvariantViolation,
    OutOfBoundsError,
    SquareEmptyError,
    SquareOccupiedError,
)
from backend.domain.pieces.registry import create_piece

WHITE_SQUARE = Coordinate(0, 0)
BLACK_SQUARE = Coordinate(4, 4)
FREE_SQUARE = Coordinate(2, 2)
UNTOUCHED_ROW = 1

TERRAIN_SIDE = 3
PAD_SQUARE = Coordinate(1, 1)
JET_PACK_SQUARE = Coordinate(0, 2)


@pytest.fixture
def populated_board(empty_board: Board, place: Callable[..., Board]) -> Board:
    """
    Give a small board holding one piece of each colour in opposite corners.

    Arguments:
        empty_board: The 5x5 board to place onto.
        place: Helper that builds and places a piece.

    Returns:
        A board with a white rook and a black rook on it.
    """
    board = place(empty_board, WHITE_SQUARE, PieceKind.ROOK, Color.WHITE)
    return place(board, BLACK_SQUARE, PieceKind.ROOK, Color.BLACK)


@pytest.fixture
def terrain_board() -> Board:
    """
    Give a 3x3 board carrying one star square and one hash square.

    Terrain and occupancy are separate fields, so a board with special squares
    is needed to prove a placement does not erase them.

    Returns:
        A board of normal squares except for the two special ones.
    """
    special = {PAD_SQUARE: Terrain.TRANSPORTER_PAD, JET_PACK_SQUARE: Terrain.JET_PACK}
    rows: list[tuple[Cell, ...]] = []
    for row in range(TERRAIN_SIDE):
        cells: list[Cell] = []
        for column in range(TERRAIN_SIDE):
            terrain = special.get(Coordinate(row, column), Terrain.NORMAL)
            cells.append(Cell(terrain=terrain))
        rows.append(tuple(cells))
    return Board.from_cells(tuple(rows))


def _add_a_piece(board: Board) -> Board:
    """
    Place a new piece on the known-free square.

    Arguments:
        board: The board to transition.

    Returns:
        A new board with one more piece on it.
    """
    piece = create_piece(piece_id=99, kind=PieceKind.KNIGHT, color=Color.BLACK)
    return board.with_piece(FREE_SQUARE, piece)


def _remove_a_piece(board: Board) -> Board:
    """
    Clear the white corner square.

    Arguments:
        board: The board to transition.

    Returns:
        A new board with one fewer piece on it.
    """
    return board.without_piece(WHITE_SQUARE)


def _relocate_a_piece(board: Board) -> Board:
    """
    Move the white corner piece to the centre.

    Arguments:
        board: The board to transition.

    Returns:
        A new board with the piece on a different square.
    """
    return board.with_piece_relocated(WHITE_SQUARE, FREE_SQUARE)


@pytest.mark.parametrize(
    "row,column,inside",
    [
        (0, 0, True),
        (2, 4, True),
        (4, 4, True),
        (5, 0, False),
        (0, 5, False),
        (9, 9, False),
    ],
)
def test_dimensions_contains_only_squares_inside_the_grid(
    small_dimensions: BoardDimensions, row: int, column: int, inside: bool
) -> None:
    """
    Report membership for well-formed coordinates on and off the grid.

    Arguments:
        small_dimensions: The 5x5 size under test.
        row: Row of the square to test.
        column: Column of the square to test.
        inside: Whether the square should be reported as present.
    """
    assert small_dimensions.contains(Coordinate(row, column)) is inside


def test_require_contains_raises_for_a_square_off_the_board(
    small_dimensions: BoardDimensions,
) -> None:
    """
    Raise OutOfBoundsError naming the square and the board that rejected it.
    """
    with pytest.raises(OutOfBoundsError) as raised:
        small_dimensions.require_contains(Coordinate(5, 2))

    assert (raised.value.row, raised.value.column) == (5, 2)


def test_require_contains_accepts_a_square_on_the_board(
    small_dimensions: BoardDimensions,
) -> None:
    """
    Pass silently for a square that exists.
    """
    small_dimensions.require_contains(Coordinate(4, 4))


@pytest.mark.parametrize("rows,columns", [(0, 5), (5, 0), (0, 0), (-1, 3)])
def test_dimensions_reject_degenerate_sizes(rows: int, columns: int) -> None:
    """
    Refuse a board with no squares in it.

    Arguments:
        rows: Row count to try.
        columns: Column count to try.
    """
    with pytest.raises(BoardSetupError):
        BoardDimensions(rows, columns)


def test_dimensions_walk_every_square_in_reading_order() -> None:
    """
    Enumerate squares row by row, which board rendering and piece walks rely on.
    """
    squares = list(BoardDimensions(2, 3).squares())

    assert squares == [
        Coordinate(0, 0),
        Coordinate(0, 1),
        Coordinate(0, 2),
        Coordinate(1, 0),
        Coordinate(1, 1),
        Coordinate(1, 2),
    ]


def test_empty_board_is_all_normal_and_unoccupied(empty_board: Board) -> None:
    """
    Build a board with no pieces and no special terrain.

    Arguments:
        empty_board: The board under test.
    """
    assert (empty_board.rows, empty_board.columns) == (5, 5)
    assert list(empty_board.pieces()) == []
    for square in empty_board.dimensions.squares():
        cell = empty_board.cell_at(square)
        assert cell.is_empty is True
        assert cell.is_occupied is False
        assert cell.terrain is Terrain.NORMAL


def test_from_cells_infers_dimensions_from_the_grid(terrain_board: Board) -> None:
    """
    Take the board size from the grid rather than requiring it twice.

    Arguments:
        terrain_board: A 3x3 grid built through from_cells.
    """
    assert terrain_board.dimensions == BoardDimensions(TERRAIN_SIDE, TERRAIN_SIDE)


def test_from_cells_rejects_a_ragged_grid() -> None:
    """
    Refuse rows of differing widths, which would break every bounds check.
    """
    ragged = ((Cell(), Cell()), (Cell(),))

    with pytest.raises(BoardSetupError):
        Board.from_cells(ragged)


@pytest.mark.parametrize("cells", [(), ((),)], ids=["no-rows", "one-empty-row"])
def test_from_cells_rejects_a_grid_with_no_cells(
    cells: tuple[tuple[Cell, ...], ...],
) -> None:
    """
    Refuse an empty grid rather than building a zero-sized board.

    Arguments:
        cells: The degenerate grid to try.
    """
    with pytest.raises(BoardSetupError):
        Board.from_cells(cells)


def test_cell_at_raises_for_a_square_off_the_board(empty_board: Board) -> None:
    """
    Treat reading a non-existent square as an error, not an empty answer.

    Arguments:
        empty_board: The board under test.
    """
    with pytest.raises(OutOfBoundsError):
        empty_board.cell_at(Coordinate(5, 5))


@pytest.mark.parametrize(
    "square,expected",
    [
        (FREE_SQUARE, True),
        (WHITE_SQUARE, False),
        (BLACK_SQUARE, False),
        (Coordinate(5, 0), False),
        (Coordinate(0, 5), False),
    ],
    ids=["empty", "own-piece", "enemy-piece", "row-off-board", "column-off-board"],
)
def test_is_empty_requires_an_unoccupied_square_in_bounds(
    populated_board: Board, square: Coordinate, expected: bool
) -> None:
    """
    Answer False for occupied squares and for squares that do not exist.

    is_empty is the gate every rule uses before stepping, so it must answer
    for out-of-bounds squares instead of raising.

    Arguments:
        populated_board: Board holding one piece of each colour.
        square: The square to test.
        expected: Whether the square should accept a piece.
    """
    assert populated_board.is_empty(square) is expected


def test_is_empty_is_true_on_special_terrain(terrain_board: Board) -> None:
    """
    Keep every terrain passable, matching the undecided meaning of "#" and "*".

    Arguments:
        terrain_board: Board carrying a star and a hash square.
    """
    assert terrain_board.is_empty(PAD_SQUARE) is True
    assert terrain_board.is_empty(JET_PACK_SQUARE) is True


@pytest.mark.parametrize(
    "square",
    [WHITE_SQUARE, FREE_SQUARE, Coordinate(5, 5)],
    ids=["friendly", "empty", "off-board"],
)
def test_enemy_at_returns_none_when_there_is_no_enemy(
    populated_board: Board, square: Coordinate
) -> None:
    """
    Answer None for a friendly piece, an empty square and a missing square.

    Arguments:
        populated_board: Board holding one piece of each colour.
        square: The square to test from white's point of view.
    """
    assert populated_board.enemy_at(square, Color.WHITE) is None


def test_enemy_at_returns_the_opposing_piece(populated_board: Board) -> None:
    """
    Answer with the occupant when it belongs to the other side.

    Arguments:
        populated_board: Board holding one piece of each colour.
    """
    found = populated_board.enemy_at(BLACK_SQUARE, Color.WHITE)

    assert found is not None
    assert found.color is Color.BLACK


def test_piece_at_and_require_piece_at_agree_on_an_occupied_square(
    populated_board: Board,
) -> None:
    """
    Give the same piece from both readers when a square is occupied.

    Arguments:
        populated_board: Board holding one piece of each colour.
    """
    assert populated_board.piece_at(WHITE_SQUARE) is populated_board.require_piece_at(WHITE_SQUARE)


def test_require_piece_at_raises_on_an_empty_square(populated_board: Board) -> None:
    """
    Treat a missing piece as a defect for callers that already proved one there.

    Arguments:
        populated_board: Board holding one piece of each colour.
    """
    assert populated_board.piece_at(FREE_SQUARE) is None
    with pytest.raises(SquareEmptyError):
        populated_board.require_piece_at(FREE_SQUARE)


def test_pieces_can_be_filtered_by_colour(populated_board: Board) -> None:
    """
    Walk occupied squares for one side or for both.

    Arguments:
        populated_board: Board holding one piece of each colour.
    """
    white = [square for square, _ in populated_board.pieces(Color.WHITE)]
    black = [square for square, _ in populated_board.pieces(Color.BLACK)]

    assert white == [WHITE_SQUARE]
    assert black == [BLACK_SQUARE]
    assert len(list(populated_board.pieces())) == 2


def test_with_piece_rejects_an_occupied_square(populated_board: Board) -> None:
    """
    Refuse to stack two pieces on one square.

    Arguments:
        populated_board: Board holding one piece of each colour.
    """
    intruder = create_piece(piece_id=77, kind=PieceKind.PAWN, color=Color.WHITE)

    with pytest.raises(SquareOccupiedError):
        populated_board.with_piece(WHITE_SQUARE, intruder)


def test_with_piece_preserves_the_squares_terrain(terrain_board: Board) -> None:
    """
    Keep special terrain under a newly placed piece.

    Arguments:
        terrain_board: Board carrying a star and a hash square.
    """
    piece = create_piece(piece_id=1, kind=PieceKind.KING, color=Color.WHITE)
    result = terrain_board.with_piece(PAD_SQUARE, piece)
    cell = result.cell_at(PAD_SQUARE)

    assert cell.piece is piece
    assert cell.terrain is Terrain.TRANSPORTER_PAD


def test_without_piece_rejects_an_empty_square(populated_board: Board) -> None:
    """
    Refuse to clear a square that holds nothing.

    Arguments:
        populated_board: Board holding one piece of each colour.
    """
    with pytest.raises(SquareEmptyError):
        populated_board.without_piece(FREE_SQUARE)


def test_without_piece_clears_the_square_and_keeps_its_terrain(
    terrain_board: Board,
) -> None:
    """
    Remove an occupant without removing the square it stood on.

    Arguments:
        terrain_board: Board carrying a star and a hash square.
    """
    piece = create_piece(piece_id=1, kind=PieceKind.KING, color=Color.BLACK)
    occupied = terrain_board.with_piece(JET_PACK_SQUARE, piece)

    cleared = occupied.without_piece(JET_PACK_SQUARE)
    cell = cleared.cell_at(JET_PACK_SQUARE)

    assert cell.piece is None
    assert cell.terrain is Terrain.JET_PACK


def test_with_piece_relocated_keeps_destination_terrain_and_marks_the_piece(
    terrain_board: Board,
) -> None:
    """
    Carry a piece onto a special square, preserving the terrain and setting
    has_moved so a pawn cannot claim its double step twice.

    Arguments:
        terrain_board: Board carrying a star and a hash square.
    """
    origin = Coordinate(0, 0)
    piece = create_piece(piece_id=1, kind=PieceKind.PAWN, color=Color.WHITE)
    board = terrain_board.with_piece(origin, piece)

    result = board.with_piece_relocated(origin, PAD_SQUARE)
    arrived = result.cell_at(PAD_SQUARE)

    assert arrived.terrain is Terrain.TRANSPORTER_PAD
    assert arrived.piece is not None
    assert arrived.piece.piece_id == piece.piece_id
    assert arrived.piece.has_moved is True
    assert result.cell_at(origin).piece is None
    assert result.cell_at(origin).terrain is Terrain.NORMAL


def test_with_piece_relocated_rejects_an_empty_origin(populated_board: Board) -> None:
    """
    Refuse to relocate a piece that is not there.

    Arguments:
        populated_board: Board holding one piece of each colour.
    """
    with pytest.raises(SquareEmptyError):
        populated_board.with_piece_relocated(FREE_SQUARE, Coordinate(3, 3))


def test_with_piece_relocated_rejects_an_occupied_destination(
    populated_board: Board,
) -> None:
    """
    Keep captures explicit by refusing to land on an occupied square.

    Arguments:
        populated_board: Board holding one piece of each colour.
    """
    with pytest.raises(SquareOccupiedError):
        populated_board.with_piece_relocated(WHITE_SQUARE, BLACK_SQUARE)


@pytest.mark.parametrize(
    "transition",
    [_add_a_piece, _remove_a_piece, _relocate_a_piece],
    ids=["with_piece", "without_piece", "with_piece_relocated"],
)
def test_transitions_never_mutate_the_source_board(
    populated_board: Board, transition: Callable[[Board], Board]
) -> None:
    """
    Hold the no-mutation invariant AI search depends on.

    Every mutator returns a new board, so exploring a branch cannot disturb the
    position it branched from. The original grid is compared cell for cell
    after the transition, not merely rendered.

    Arguments:
        populated_board: Board holding one piece of each colour.
        transition: The mutator under test.
    """
    cells_before = populated_board.cells
    rendered_before = str(populated_board)

    result = transition(populated_board)

    assert result is not populated_board
    assert populated_board.cells is cells_before
    assert populated_board.cells == cells_before
    assert str(populated_board) == rendered_before
    assert str(result) != rendered_before
    # Untouched rows are shared, since every cell is immutable.
    assert result.cells[UNTOUCHED_ROW] is populated_board.cells[UNTOUCHED_ROW]


def test_relocation_does_not_mark_the_source_boards_piece_as_moved(
    populated_board: Board,
) -> None:
    """
    Keep has_moved off the original piece, since Piece.moved returns a copy.

    Arguments:
        populated_board: Board holding one piece of each colour.
    """
    result = populated_board.with_piece_relocated(WHITE_SQUARE, FREE_SQUARE)

    assert populated_board.require_piece_at(WHITE_SQUARE).has_moved is False
    assert result.require_piece_at(FREE_SQUARE).has_moved is True


def test_validate_accepts_a_well_formed_board(populated_board: Board) -> None:
    """
    Pass silently when every structural invariant holds.

    Arguments:
        populated_board: Board holding one piece of each colour.
    """
    populated_board.validate()


def test_validate_rejects_a_duplicated_piece_identity() -> None:
    """
    Raise InvariantViolation when one piece id appears on two squares.

    Piece identity is what lets an effect name the piece it displaced, so a
    duplicate is an engine defect rather than bad input.
    """
    piece = create_piece(piece_id=7, kind=PieceKind.ROOK, color=Color.WHITE)
    board = Board.from_cells(((Cell(piece=piece), Cell(piece=piece)),))

    with pytest.raises(InvariantViolation) as raised:
        board.validate()

    assert "7" in str(raised.value)


def test_validate_rejects_a_grid_that_disagrees_with_its_dimensions() -> None:
    """
    Catch a board assembled past from_cells whose rows do not match its size.
    """
    board = Board(dimensions=BoardDimensions(3, 2), cells=((Cell(), Cell()),))

    with pytest.raises(InvariantViolation):
        board.validate()


def test_board_renders_terrain_and_pieces(terrain_board: Board) -> None:
    """
    Render one line per row, using terrain symbols for empty squares.

    Arguments:
        terrain_board: Board carrying a star and a hash square.
    """
    piece = create_piece(piece_id=1, kind=PieceKind.ROOK, color=Color.BLACK)
    board = terrain_board.with_piece(Coordinate(2, 0), piece)

    assert str(board) == "..#\n.*.\nr.."
