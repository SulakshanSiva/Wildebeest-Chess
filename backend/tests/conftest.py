from collections.abc import Callable, Iterable, Iterator
from itertools import count

import pytest

from backend.domain.board import Board, BoardDimensions
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, PieceKind
from backend.domain.move import Move
from backend.domain.pieces.base import Piece
from backend.domain.pieces.registry import create_piece
from backend.domain.variant import Variant

# Fixture boards are deliberately small. Piece rules must hold on any board
# size, so proving them on 5x5 also proves they are not hard-coded to 11x11.
SMALL_BOARD_SIDE = 5


@pytest.fixture
def small_dimensions() -> BoardDimensions:
    """
    Give the dimensions every focused rule fixture is built on.

    Returns:
        A square 5x5 board size.
    """
    return BoardDimensions(SMALL_BOARD_SIDE, SMALL_BOARD_SIDE)


@pytest.fixture
def empty_board(small_dimensions: BoardDimensions) -> Board:
    """
    Give a small board of empty, normal squares.

    Arguments:
        small_dimensions: Size of the board to build.

    Returns:
        A 5x5 board with nothing on it.
    """
    return Board.empty(small_dimensions)


@pytest.fixture
def centre() -> Coordinate:
    """
    Give the middle square of the small fixture board.

    Returns:
        The coordinate every unobstructed-reach test starts from.
    """
    return Coordinate(2, 2)


@pytest.fixture
def piece_ids() -> Iterator[int]:
    """
    Supply unique piece identities for one test.

    A fresh counter per test keeps ids distinct so Board.validate never trips
    on an accidental duplicate.

    Returns:
        An endless counter starting at one.
    """
    return count(1)


@pytest.fixture
def place(piece_ids: Iterator[int]) -> Callable[..., Board]:
    """
    Give a helper that places a new piece on a board.

    Arguments:
        piece_ids: Counter supplying the next piece identity.

    Returns:
        A callable taking a board, a square, a kind and a colour.
    """

    def _place(
        board: Board,
        square: Coordinate,
        kind: PieceKind,
        color: Color,
        *,
        has_moved: bool = False,
    ) -> Board:
        """
        Place a freshly built piece and return the resulting board.

        Arguments:
            board: Board to place onto.
            square: Where the piece goes.
            kind: What type of piece to build.
            color: Which side owns it.
            has_moved: Whether the piece has already moved.

        Returns:
            A new board carrying the piece.
        """
        piece = create_piece(
            piece_id=next(piece_ids),
            kind=kind,
            color=color,
            has_moved=has_moved,
        )
        return board.with_piece(square, piece)

    return _place


@pytest.fixture
def candidates_for() -> Callable[[Board, Coordinate], tuple[Move, ...]]:
    """
    Give a helper that asks the piece on a square for its candidate moves.

    Returns:
        A callable taking a board and an origin square.
    """

    def _candidates_for(board: Board, origin: Coordinate) -> tuple[Move, ...]:
        """
        Generate the candidates of whichever piece stands on a square.

        Arguments:
            board: Board to read.
            origin: Square of the piece being asked.

        Returns:
            The candidate moves the piece's own rule produces.
        """
        piece: Piece = board.require_piece_at(origin)
        return piece.movement.candidates(board, origin)

    return _candidates_for


@pytest.fixture
def destinations() -> Callable[[Iterable[Move]], set[Coordinate]]:
    """
    Give a helper that reduces moves to the squares they reach.

    Returns:
        A callable turning any iterable of moves into a set of destinations.
    """

    def _destinations(moves: Iterable[Move]) -> set[Coordinate]:
        """
        Collect the destination square of every move.

        Arguments:
            moves: The moves to reduce.

        Returns:
            The set of squares those moves land on.
        """
        return {move.destination for move in moves}

    return _destinations


@pytest.fixture
def wildebeest_board() -> Board:
    """
    Build the full 11x11 starting board from the shipped variant.

    Returns:
        The validated starting board.
    """
    return Variant().build_board()
