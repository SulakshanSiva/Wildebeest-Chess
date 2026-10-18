from __future__ import annotations

import pytest

from backend.domain.board import Board, BoardDimensions, Cell
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, PieceKind, Terrain
from backend.domain.errors import InvariantViolation
from backend.domain.pieces.movement import SlideRule
from backend.domain.pieces.registry import create_piece
from backend.domain.rules.terrain import (
    apply_transporters,
    jet_pack_landing,
    occupied_pads,
    validate_links,
)
from backend.domain.variant import WILDEBEEST_TRANSPORTER_LINKS, Variant

PAD_A = Coordinate(0, 0)
PAD_B = Coordinate(2, 2)
TWO_PADS = {PAD_A: PAD_B, PAD_B: PAD_A}

NON_KING_KINDS = [kind for kind in PieceKind if kind is not PieceKind.KING]


@pytest.fixture
def pad_board() -> Board:
    """
    Give a 3x3 board with transporter pads on two opposite corners.

    Returns:
        A board whose only special terrain is the two pads.
    """
    dimensions = BoardDimensions(3, 3)
    rows = []
    for row in range(dimensions.rows):
        cells = []
        for column in range(dimensions.columns):
            square = Coordinate(row, column)
            terrain = Terrain.TRANSPORTER_PAD if square in TWO_PADS else Terrain.NORMAL
            cells.append(Cell(terrain=terrain))
        rows.append(tuple(cells))
    return Board.from_cells(tuple(rows))


def test_a_king_landing_on_a_jet_pack_becomes_a_jet_pack_king() -> None:
    """
    Upgrade a King that lands on a jet pack, which is how the piece enters play.
    """
    king = create_piece(piece_id=7, kind=PieceKind.KING, color=Color.BLACK, has_moved=True)

    upgraded = jet_pack_landing(king)

    assert upgraded.kind is PieceKind.JET_PACK_KING
    assert isinstance(upgraded.movement, SlideRule)


def test_the_upgrade_keeps_identity_colour_and_first_move_state() -> None:
    """
    Carry the King's identity across the upgrade; it is the same piece, changed.
    """
    king = create_piece(piece_id=7, kind=PieceKind.KING, color=Color.BLACK, has_moved=True)

    upgraded = jet_pack_landing(king)

    assert upgraded.piece_id == king.piece_id
    assert upgraded.color is king.color
    assert upgraded.has_moved is king.has_moved


@pytest.mark.parametrize("kind", NON_KING_KINDS, ids=lambda kind: kind.value)
def test_only_a_king_is_upgraded_by_a_jet_pack(kind: PieceKind) -> None:
    """
    Leave every other piece untouched by the jet pack.

    Arguments:
        kind: The non-King piece kind under test.
    """
    piece = create_piece(piece_id=1, kind=kind, color=Color.WHITE)

    assert jet_pack_landing(piece) is piece


def test_an_empty_pad_moves_nothing(pad_board: Board) -> None:
    """
    Return the same board when no pad is occupied, doing no work.
    """
    assert apply_transporters(pad_board, TWO_PADS) is pad_board


def test_occupied_pads_reports_only_pads_holding_a_piece(pad_board: Board) -> None:
    """
    Narrow the links to those that will actually move something.

    Arguments:
        pad_board: A 3x3 board with two pads.
    """
    piece = create_piece(piece_id=1, kind=PieceKind.ROOK, color=Color.WHITE)
    board = pad_board.with_piece(PAD_A, piece)

    assert occupied_pads(board, TWO_PADS) == {PAD_A: PAD_B}


def test_one_occupied_pad_relocates_its_piece(pad_board: Board) -> None:
    """
    Move a lone pad occupant to the square its pad leads to.

    Arguments:
        pad_board: A 3x3 board with two pads.
    """
    piece = create_piece(piece_id=1, kind=PieceKind.ROOK, color=Color.WHITE)
    board = pad_board.with_piece(PAD_A, piece)

    result = apply_transporters(board, TWO_PADS)

    assert result.piece_at(PAD_A) is None
    assert result.require_piece_at(PAD_B).piece_id == 1


def test_two_occupied_pads_swap_simultaneously(pad_board: Board) -> None:
    """
    Exchange two pad occupants at once rather than one after the other.

    Sequential relocation would fail here: the first piece cannot move onto a
    square the second has not vacated yet.

    Arguments:
        pad_board: A 3x3 board with two pads.
    """
    first = create_piece(piece_id=1, kind=PieceKind.ROOK, color=Color.WHITE)
    second = create_piece(piece_id=2, kind=PieceKind.KNIGHT, color=Color.BLACK)
    board = pad_board.with_piece(PAD_A, first).with_piece(PAD_B, second)

    result = apply_transporters(board, TWO_PADS)

    assert result.require_piece_at(PAD_A).piece_id == 2
    assert result.require_piece_at(PAD_B).piece_id == 1


def test_transporting_does_not_mutate_the_source_board(pad_board: Board) -> None:
    """
    Leave the original board untouched, as every other transition does.

    Arguments:
        pad_board: A 3x3 board with two pads.
    """
    piece = create_piece(piece_id=1, kind=PieceKind.ROOK, color=Color.WHITE)
    board = pad_board.with_piece(PAD_A, piece)
    before = str(board)
    cells_before = board.cells

    apply_transporters(board, TWO_PADS)

    assert board.cells is cells_before
    assert str(board) == before


def test_transporting_preserves_the_terrain_of_both_squares(pad_board: Board) -> None:
    """
    Keep each pad a pad after a piece arrives on or leaves it.

    Arguments:
        pad_board: A 3x3 board with two pads.
    """
    piece = create_piece(piece_id=1, kind=PieceKind.ROOK, color=Color.WHITE)
    board = pad_board.with_piece(PAD_A, piece)

    result = apply_transporters(board, TWO_PADS)

    assert result.cell_at(PAD_A).terrain is Terrain.TRANSPORTER_PAD
    assert result.cell_at(PAD_B).terrain is Terrain.TRANSPORTER_PAD


def test_the_shipped_links_rotate_all_four_pads_at_once() -> None:
    """
    Rotate four occupied pads through the shipped four-cycle in one step.

    This is the whole-board version of the swap: every pad is occupied, so a
    sequential implementation would collide on every single move.
    """
    board = Variant().build_board()
    for index, square in enumerate(WILDEBEEST_TRANSPORTER_LINKS, start=900):
        board = board.with_piece(
            square,
            create_piece(piece_id=index, kind=PieceKind.ROOK, color=Color.WHITE),
        )
    before = {
        square: board.require_piece_at(square).piece_id for square in WILDEBEEST_TRANSPORTER_LINKS
    }

    result = apply_transporters(board, WILDEBEEST_TRANSPORTER_LINKS)

    for source, target in WILDEBEEST_TRANSPORTER_LINKS.items():
        assert result.require_piece_at(target).piece_id == before[source]


def test_the_shipped_links_form_a_single_four_cycle() -> None:
    """
    Pin the cycle: following the links from any pad visits all four and returns.
    """
    start = Coordinate(3, 1)
    visited = [start]
    square = WILDEBEEST_TRANSPORTER_LINKS[start]
    while square != start:
        visited.append(square)
        square = WILDEBEEST_TRANSPORTER_LINKS[square]

    assert visited == [Coordinate(3, 1), Coordinate(7, 9), Coordinate(7, 1), Coordinate(3, 9)]


def test_links_that_are_not_a_permutation_are_rejected(pad_board: Board) -> None:
    """
    Refuse links where two pads lead to one square, which would stack pieces.

    Arguments:
        pad_board: A 3x3 board with two pads.
    """
    with pytest.raises(InvariantViolation, match="same square"):
        validate_links(pad_board, {PAD_A: PAD_B, PAD_B: PAD_B})


def test_links_referencing_a_non_pad_square_are_rejected(pad_board: Board) -> None:
    """
    Refuse links anchored on ordinary squares rather than pads.

    Arguments:
        pad_board: A 3x3 board with two pads.
    """
    ordinary = Coordinate(1, 1)
    with pytest.raises(InvariantViolation):
        validate_links(pad_board, {ordinary: PAD_A, PAD_A: ordinary})


def test_a_pad_left_unlinked_is_rejected(pad_board: Board) -> None:
    """
    Refuse a board with a pad no link covers, which would be an inert pad.

    Arguments:
        pad_board: A 3x3 board with two pads.
    """
    with pytest.raises(InvariantViolation):
        validate_links(pad_board, {PAD_A: PAD_A})


def test_the_shipped_variant_validates_its_own_links() -> None:
    """
    Accept the shipped board and links together, which build_board checks.
    """
    board = Variant().build_board()

    validate_links(board, WILDEBEEST_TRANSPORTER_LINKS)


def test_the_jet_pack_upgrades_both_players_kings() -> None:
    """
    Upgrade either side's King, since the jet pack is not consumed by the first.

    The function takes a piece and returns a piece without touching the board,
    so there is no state that a first use could exhaust.
    """
    white_king = create_piece(piece_id=1, kind=PieceKind.KING, color=Color.WHITE)
    black_king = create_piece(piece_id=2, kind=PieceKind.KING, color=Color.BLACK)

    assert jet_pack_landing(white_king).kind is PieceKind.JET_PACK_KING
    assert jet_pack_landing(black_king).kind is PieceKind.JET_PACK_KING


def test_a_jet_pack_square_stays_a_jet_pack_after_an_upgrade(pad_board: Board) -> None:
    """
    Leave the terrain untouched when a King is upgraded on it.

    Arguments:
        pad_board: A 3x3 board, used here only for its ordinary squares.
    """
    square = Coordinate(1, 1)
    jet_pack_board = Board.from_cells(
        tuple(
            tuple(
                Cell(terrain=Terrain.JET_PACK)
                if Coordinate(row, column) == square
                else pad_board.cells[row][column]
                for column in range(pad_board.columns)
            )
            for row in range(pad_board.rows)
        )
    )
    king = create_piece(piece_id=1, kind=PieceKind.KING, color=Color.WHITE)
    occupied = jet_pack_board.with_piece(square, king)

    upgraded = occupied.without_piece(square).with_piece(square, jet_pack_landing(king))

    assert upgraded.cell_at(square).terrain is Terrain.JET_PACK
    assert upgraded.require_piece_at(square).kind is PieceKind.JET_PACK_KING


def test_a_jet_pack_king_moves_exactly_like_a_bishop() -> None:
    """
    Pin the confirmed rule that a king with a jet pack moves as a bishop.

    Asserted as an equivalence rather than by listing squares, so the two can
    never drift apart without this failing.
    """
    board = Board.empty(BoardDimensions(5, 5))
    origin = Coordinate(2, 2)

    bishop_board = board.with_piece(
        origin, create_piece(piece_id=1, kind=PieceKind.BISHOP, color=Color.WHITE)
    )
    jet_king_board = board.with_piece(
        origin, create_piece(piece_id=2, kind=PieceKind.JET_PACK_KING, color=Color.WHITE)
    )

    bishop_piece = bishop_board.require_piece_at(origin)
    jet_king_piece = jet_king_board.require_piece_at(origin)

    bishop_squares = {
        move.destination for move in bishop_piece.movement.candidates(bishop_board, origin)
    }
    jet_king_squares = {
        move.destination for move in jet_king_piece.movement.candidates(jet_king_board, origin)
    }

    assert jet_king_squares == bishop_squares
    assert jet_king_squares


def test_transport_does_not_consume_a_pieces_first_move(pad_board: Board) -> None:
    """
    Carry an unmoved piece across a pad without marking it as having moved.

    Confirmed rule: being transported is not a move the piece made, so a pawn
    that has never moved still has its double step afterwards.

    Arguments:
        pad_board: A 3x3 board with two pads.
    """
    pawn = create_piece(piece_id=1, kind=PieceKind.PAWN, color=Color.WHITE, has_moved=False)
    board = pad_board.with_piece(PAD_A, pawn)

    result = apply_transporters(board, TWO_PADS)

    assert result.require_piece_at(PAD_B).has_moved is False


def test_transport_preserves_an_already_moved_flag(pad_board: Board) -> None:
    """
    Leave the flag alone in the other direction too, rather than clearing it.

    Arguments:
        pad_board: A 3x3 board with two pads.
    """
    rook = create_piece(piece_id=1, kind=PieceKind.ROOK, color=Color.WHITE, has_moved=True)
    board = pad_board.with_piece(PAD_A, rook)

    result = apply_transporters(board, TWO_PADS)

    assert result.require_piece_at(PAD_B).has_moved is True
