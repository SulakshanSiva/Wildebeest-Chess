from __future__ import annotations

from collections.abc import Callable

from backend.domain.board import Board
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, PieceKind
from backend.domain.rules.move_generator import legal_moves, moves_for_piece
from backend.domain.variant import Variant


def test_a_paralysed_piece_has_no_moves(empty_board: Board, place: Callable[..., Board]) -> None:
    """
    Hold a piece beside an enemy BeeKeeper, so it offers nothing.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.ROOK, Color.BLACK)
    board = place(board, Coordinate(2, 3), PieceKind.BEEKEEPER, Color.WHITE)

    assert moves_for_piece(board, Coordinate(2, 2)) == ()


def test_a_paralysed_piece_can_still_be_flung(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Let a friendly Catapult launch a paralysed piece, as the rules allow.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.CATAPULT, Color.BLACK)
    board = place(board, Coordinate(2, 1), PieceKind.ROOK, Color.BLACK)
    board = place(board, Coordinate(1, 0), PieceKind.BEEKEEPER, Color.WHITE)

    moves = legal_moves(board, Color.BLACK)

    assert any(move.origin == Coordinate(2, 1) for move in moves)
    assert moves_for_piece(board, Coordinate(2, 1)) == ()


def test_legal_moves_cover_only_the_side_asked_for(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Offer a colour's moves and none of its opponent's.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(0, 0), PieceKind.ROOK, Color.WHITE)
    board = place(board, Coordinate(4, 4), PieceKind.ROOK, Color.BLACK)

    assert {move.actor for move in legal_moves(board, Color.WHITE)} == {Coordinate(0, 0)}
    assert {move.actor for move in legal_moves(board, Color.BLACK)} == {Coordinate(4, 4)}


def test_moves_are_not_filtered_for_what_they_expose(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Keep a move that walks a King into danger, since the rules have no check.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.KING, Color.WHITE)
    board = place(board, Coordinate(2, 4), PieceKind.ROOK, Color.BLACK)

    destinations = {move.destination for move in legal_moves(board, Color.WHITE)}

    assert Coordinate(2, 3) in destinations


def test_every_piece_can_be_asked_on_the_starting_board() -> None:
    """
    Generate moves for every piece of the opening position without error.
    """
    board = Variant().build_board()

    for side in (Color.WHITE, Color.BLACK):
        assert legal_moves(board, side)
