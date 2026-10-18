import pytest

from backend.domain.board import Board
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, PieceKind, Terrain
from backend.domain.errors import BoardSetupError, UnknownPieceSymbolError
from backend.domain.variant import WILDEBEEST_LAYOUT, Variant, parse_layout

BOARD_SIDE = 11
TOTAL_PIECES = 44
PIECES_PER_COLOUR = 22

EXPECTED_PAD_SQUARES = {
    Coordinate(3, 1),
    Coordinate(3, 9),
    Coordinate(7, 1),
    Coordinate(7, 9),
}
EXPECTED_JET_PACK_SQUARES = {Coordinate(5, 5)}

# A deliberately non-square, non-11x11 layout, proving rules and parsing are
# not tied to the shipped board size.
CUSTOM_LAYOUT = """
rnk
*p.
.*P
..K
"""

# Two pads on the custom board, swapping with each other. A two-cycle is the
# smallest permutation that actually moves anything.
CUSTOM_LINKS = {
    Coordinate(1, 0): Coordinate(2, 1),
    Coordinate(2, 1): Coordinate(1, 0),
}


def test_layout_survives_the_round_trip_through_a_board(wildebeest_board: Board) -> None:
    """
    Render the parsed starting board back into exactly its own layout text.

    This is the parsing and serialisation round trip: any symbol, terrain or
    colour the parser drops would show up as a diff here.

    Arguments:
        wildebeest_board: The parsed starting board.
    """
    assert str(wildebeest_board) == WILDEBEEST_LAYOUT.strip()


def test_starting_board_is_eleven_by_eleven(wildebeest_board: Board) -> None:
    """
    Keep the shipped board at its documented size.

    Arguments:
        wildebeest_board: The parsed starting board.
    """
    assert (wildebeest_board.rows, wildebeest_board.columns) == (BOARD_SIDE, BOARD_SIDE)


def test_starting_board_is_structurally_valid(wildebeest_board: Board) -> None:
    """
    Pass the board's own invariant check after setup.

    Arguments:
        wildebeest_board: The parsed starting board.
    """
    wildebeest_board.validate()


@pytest.mark.parametrize(
    "color,expected",
    [(None, TOTAL_PIECES), (Color.WHITE, PIECES_PER_COLOUR), (Color.BLACK, PIECES_PER_COLOUR)],
    ids=["both-sides", "white", "black"],
)
def test_starting_board_has_a_balanced_army(
    wildebeest_board: Board, color: Color | None, expected: int
) -> None:
    """
    Count the pieces the layout places, in total and per side.

    Arguments:
        wildebeest_board: The parsed starting board.
        color: Side to count, or None for both.
        expected: How many pieces that query should find.
    """
    assert len(list(wildebeest_board.pieces(color))) == expected


def test_white_starts_on_the_low_rows_and_black_on_the_high_rows(
    wildebeest_board: Board,
) -> None:
    """
    Keep case-encoded colour aligned with the direction pawns advance.

    Arguments:
        wildebeest_board: The parsed starting board.
    """
    white_rows = {square.row for square, _ in wildebeest_board.pieces(Color.WHITE)}
    black_rows = {square.row for square, _ in wildebeest_board.pieces(Color.BLACK)}

    assert white_rows == {0, 1}
    assert black_rows == {9, 10}


def test_terrain_is_preserved_by_parsing(wildebeest_board: Board) -> None:
    """
    Record the special squares as terrain rather than discarding them.

    Arguments:
        wildebeest_board: The parsed starting board.
    """
    found: dict[Terrain, set[Coordinate]] = {
        Terrain.TRANSPORTER_PAD: set(),
        Terrain.JET_PACK: set(),
    }
    for square in wildebeest_board.dimensions.squares():
        terrain = wildebeest_board.cell_at(square).terrain
        if terrain is not Terrain.NORMAL:
            found[terrain].add(square)

    assert found[Terrain.TRANSPORTER_PAD] == EXPECTED_PAD_SQUARES
    assert found[Terrain.JET_PACK] == EXPECTED_JET_PACK_SQUARES


def test_special_squares_are_unoccupied_at_setup(wildebeest_board: Board) -> None:
    """
    Leave the special squares empty, since the layout cannot express a piece
    standing on one.

    Arguments:
        wildebeest_board: The parsed starting board.
    """
    for square in EXPECTED_PAD_SQUARES | EXPECTED_JET_PACK_SQUARES:
        assert wildebeest_board.piece_at(square) is None


def test_every_starting_piece_has_a_unique_identity(wildebeest_board: Board) -> None:
    """
    Number the pieces consecutively and without repeats.

    Arguments:
        wildebeest_board: The parsed starting board.
    """
    ids = [piece.piece_id for _, piece in wildebeest_board.pieces()]

    assert len(set(ids)) == TOTAL_PIECES
    assert sorted(ids) == list(range(1, TOTAL_PIECES + 1))


def test_parse_layout_can_start_identities_from_any_number() -> None:
    """
    Offset piece identities so two boards can be built without id collisions.
    """
    board = parse_layout(CUSTOM_LAYOUT, first_piece_id=100)
    ids = sorted(piece.piece_id for _, piece in board.pieces())

    assert ids[0] == 100
    assert ids == list(range(100, 100 + len(ids)))


def test_parse_layout_handles_a_small_custom_layout() -> None:
    """
    Parse a layout that is neither square nor 11x11, so piece rules can be
    tested on cheap fixtures.
    """
    board = parse_layout(CUSTOM_LAYOUT)

    assert (board.rows, board.columns) == (4, 3)
    assert board.cell_at(Coordinate(2, 1)).terrain is Terrain.TRANSPORTER_PAD
    assert board.require_piece_at(Coordinate(0, 0)).kind is PieceKind.ROOK
    assert board.require_piece_at(Coordinate(0, 0)).color is Color.BLACK
    assert board.require_piece_at(Coordinate(2, 2)).color is Color.WHITE
    assert board.require_piece_at(Coordinate(3, 2)).kind is PieceKind.KING
    assert str(board) == CUSTOM_LAYOUT.strip()


@pytest.mark.parametrize(
    "layout",
    ["RNB\nRN", "..\n...\n..", "\n"],
    ids=["short-last-row", "wide-middle-row", "blank"],
)
def test_parse_layout_rejects_a_layout_it_cannot_make_rectangular(layout: str) -> None:
    """
    Refuse ragged or empty layouts instead of guessing the board size.

    Arguments:
        layout: The malformed layout text.
    """
    with pytest.raises(BoardSetupError):
        parse_layout(layout)


@pytest.mark.parametrize(
    "symbol",
    ["?", "Q", "q", "1", " ", "-"],
    ids=["question", "upper-unknown", "lower-unknown", "digit", "space", "dash"],
)
def test_parse_layout_rejects_an_unknown_symbol(symbol: str) -> None:
    """
    Name the offending character and where it appeared.

    Arguments:
        symbol: The character with no registered meaning.
    """
    # The symbol goes mid-layout: a trailing space would be stripped away
    # before the parser ever saw it.
    layout = f".{symbol}\n.."

    with pytest.raises(UnknownPieceSymbolError) as raised:
        parse_layout(layout)

    assert raised.value.symbol == symbol
    assert isinstance(raised.value, BoardSetupError)


def test_unknown_symbol_error_is_a_board_setup_error() -> None:
    """
    Keep the symbol failure inside the setup error family, so one handler at
    the API boundary covers both.
    """
    assert issubclass(UnknownPieceSymbolError, BoardSetupError)


def test_variant_defaults_describe_the_shipped_game() -> None:
    """
    Expose the variant identity the API reports, with white to move first.
    """
    variant = Variant()

    assert variant.variant_id == "wildebeest"
    assert variant.name == "Wildebeest Chess"
    assert variant.first_player is Color.WHITE
    assert variant.layout == WILDEBEEST_LAYOUT


def test_initial_position_starts_with_white_to_move() -> None:
    """
    Build the opening position from the layout, at ply zero.
    """
    position = Variant().initial_position()

    assert position.side_to_move is Color.WHITE
    assert position.ply == 0
    assert str(position.board) == WILDEBEEST_LAYOUT.strip()


def test_a_variant_can_be_built_from_another_layout() -> None:
    """
    Keep the layout a field rather than a constant, so other boards are loadable.
    """
    variant = Variant(
        variant_id="tiny",
        name="Tiny",
        layout=CUSTOM_LAYOUT,
        first_player=Color.BLACK,
        transporter_links=dict(CUSTOM_LINKS),
    )
    position = variant.initial_position()

    assert position.side_to_move is Color.BLACK
    assert (position.board.rows, position.board.columns) == (4, 3)


def test_build_board_returns_an_independent_board_each_time() -> None:
    """
    Hand out a fresh board per call, so one game cannot disturb another.
    """
    variant = Variant()
    first = variant.build_board()
    second = variant.build_board()

    assert first is not second
    assert str(first) == str(second)
