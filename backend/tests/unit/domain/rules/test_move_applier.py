from __future__ import annotations

from collections.abc import Callable

import pytest

from backend.domain.board import Board
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, PieceKind
from backend.domain.move import Move
from backend.domain.rules.move_applier import apply_move

CENTRE = Coordinate(2, 2)
EAST = Coordinate(2, 3)
FAR_EAST = Coordinate(2, 4)
WEST = Coordinate(2, 1)


def test_a_plain_move_relocates_and_marks_the_piece_moved(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Move a piece onto an empty square and record that it has moved.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, CENTRE, PieceKind.ROOK, Color.WHITE)

    result = apply_move(board, Move.simple(CENTRE, EAST, capture=False))

    assert result.piece_at(CENTRE) is None
    assert result.require_piece_at(EAST).has_moved is True


def test_a_capture_removes_the_victim(empty_board: Board, place: Callable[..., Board]) -> None:
    """
    Replace the enemy on the destination with the capturing piece.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, CENTRE, PieceKind.ROOK, Color.WHITE)
    board = place(board, EAST, PieceKind.PAWN, Color.BLACK)

    result = apply_move(board, Move.simple(CENTRE, EAST, capture=True))

    assert result.require_piece_at(EAST).kind is PieceKind.ROOK
    assert len(list(result.pieces())) == 1


def test_a_push_moves_both_pieces(empty_board: Board, place: Callable[..., Board]) -> None:
    """
    Shove the occupant one square on and step the Gorilla into its place.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)
    board = place(board, EAST, PieceKind.ROOK, Color.BLACK)

    result = apply_move(board, Move.push(CENTRE, EAST, FAR_EAST))

    assert result.require_piece_at(EAST).kind is PieceKind.GORILLA
    assert result.require_piece_at(FAR_EAST).kind is PieceKind.ROOK
    assert result.piece_at(CENTRE) is None


def test_a_shoved_piece_keeps_its_first_move(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Leave a pushed pawn unmoved, since the Gorilla spent the turn, not the pawn.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)
    board = place(board, EAST, PieceKind.PAWN, Color.BLACK)

    result = apply_move(board, Move.push(CENTRE, EAST, FAR_EAST))

    assert result.require_piece_at(FAR_EAST).has_moved is False
    assert result.require_piece_at(EAST).has_moved is True


def test_a_crush_destroys_the_occupant(empty_board: Board, place: Callable[..., Board]) -> None:
    """
    Remove the piece that could not be pushed and put the Gorilla on its square.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)
    board = place(board, EAST, PieceKind.PAWN, Color.BLACK)
    board = place(board, FAR_EAST, PieceKind.ROOK, Color.WHITE)

    result = apply_move(board, Move.crush(CENTRE, EAST))

    assert result.require_piece_at(EAST).kind is PieceKind.GORILLA
    assert result.require_piece_at(FAR_EAST).kind is PieceKind.ROOK
    assert len(list(result.pieces())) == 2


def test_a_fling_leaves_the_catapult_in_place(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Launch the passenger over the Catapult and keep the Catapult where it was.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, CENTRE, PieceKind.CATAPULT, Color.WHITE)
    board = place(board, WEST, PieceKind.ROOK, Color.WHITE)

    result = apply_move(board, Move.fling(CENTRE, WEST, FAR_EAST))

    assert result.require_piece_at(CENTRE).kind is PieceKind.CATAPULT
    assert result.require_piece_at(FAR_EAST).kind is PieceKind.ROOK
    assert result.piece_at(WEST) is None


def test_a_flung_piece_keeps_its_first_move(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Leave a flung pawn unmoved, since the Catapult spent the turn.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, CENTRE, PieceKind.CATAPULT, Color.WHITE)
    board = place(board, WEST, PieceKind.PAWN, Color.WHITE)

    result = apply_move(board, Move.fling(CENTRE, WEST, FAR_EAST))

    assert result.require_piece_at(FAR_EAST).has_moved is False


def test_a_fling_can_capture_on_landing(empty_board: Board, place: Callable[..., Board]) -> None:
    """
    Remove an enemy that the flung piece lands on.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, CENTRE, PieceKind.CATAPULT, Color.WHITE)
    board = place(board, WEST, PieceKind.ROOK, Color.WHITE)
    board = place(board, FAR_EAST, PieceKind.PAWN, Color.BLACK)

    result = apply_move(board, Move.fling(CENTRE, WEST, FAR_EAST))

    assert result.require_piece_at(FAR_EAST).kind is PieceKind.ROOK
    assert len(list(result.pieces())) == 2


@pytest.mark.parametrize(
    "move",
    [Move.simple(CENTRE, WEST, capture=False), Move.push(CENTRE, EAST, FAR_EAST)],
    ids=["move", "push"],
)
def test_applying_a_move_never_mutates_the_source_board(
    empty_board: Board, place: Callable[..., Board], move: Move
) -> None:
    """
    Keep the source board untouched, the property the AI search relies on.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        move: The move to apply.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)
    board = place(board, EAST, PieceKind.PAWN, Color.BLACK)
    cells_before = board.cells
    rendered_before = str(board)

    apply_move(board, move)

    assert board.cells is cells_before
    assert str(board) == rendered_before
