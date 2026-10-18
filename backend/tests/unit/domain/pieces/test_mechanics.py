from __future__ import annotations

from collections.abc import Callable, Iterable

import pytest

from backend.domain.board import Board
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, MoveAction, PieceKind
from backend.domain.move import Move

CENTRE = Coordinate(2, 2)
EAST = Coordinate(2, 3)
FAR_EAST = Coordinate(2, 4)
WEST = Coordinate(2, 1)


def _actions(moves: Iterable[Move]) -> set[MoveAction]:
    """
    Reduce moves to the set of actions they use.

    Arguments:
        moves: The moves to inspect.

    Returns:
        Every distinct action present.
    """
    return {move.action for move in moves}


def _to(moves: Iterable[Move], square: Coordinate) -> Move:
    """
    Find the single move landing on a square.

    Arguments:
        moves: The moves to search.
        square: The destination wanted.

    Returns:
        The one move with that destination.
    """
    found = [move for move in moves if move.destination == square]
    assert len(found) == 1, f"expected exactly one move to {square}, got {len(found)}"
    return found[0]


def test_a_gorilla_steps_onto_an_empty_square(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Move the Gorilla like a King when nothing is in the way.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)

    moves = candidates_for(board, CENTRE)

    assert len(moves) == 8
    assert _actions(moves) == {MoveAction.MOVE}


@pytest.mark.parametrize("colour", [Color.WHITE, Color.BLACK], ids=["friendly", "enemy"])
def test_a_gorilla_pushes_either_colour(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    colour: Color,
) -> None:
    """
    Push friendly and opposing pieces alike, as the rules require.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        colour: Colour of the piece being pushed.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)
    board = place(board, EAST, PieceKind.PAWN, colour)

    move = _to(candidates_for(board, CENTRE), EAST)

    assert move.action is MoveAction.PUSH
    assert move.displaced is not None
    assert move.displaced.origin == EAST
    assert move.displaced.destination == FAR_EAST


def test_a_gorilla_never_captures_by_stepping_on(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Emit no plain capture anywhere, since a Gorilla does not capture.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)
    board = place(board, EAST, PieceKind.PAWN, Color.BLACK)
    board = place(board, WEST, PieceKind.ROOK, Color.BLACK)

    assert MoveAction.CAPTURE not in _actions(candidates_for(board, CENTRE))


def test_a_gorilla_crushes_a_piece_it_cannot_push_onward(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Destroy the pushed piece when the square beyond it is occupied.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)
    board = place(board, EAST, PieceKind.PAWN, Color.BLACK)
    board = place(board, FAR_EAST, PieceKind.ROOK, Color.WHITE)

    move = _to(candidates_for(board, CENTRE), EAST)

    assert move.action is MoveAction.CRUSH
    assert move.displaced is None


def test_a_gorilla_cannot_push_another_gorilla(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Leave another Gorilla immovable, friendly or not.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)
    board = place(board, EAST, PieceKind.GORILLA, Color.BLACK)

    assert not [move for move in candidates_for(board, CENTRE) if move.destination == EAST]


def test_a_gorilla_cannot_push_a_hovering_jet_pack_king(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Leave a hovering piece alone; it floats clear of the shove.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)
    board = place(board, EAST, PieceKind.JET_PACK_KING, Color.BLACK)

    assert not [move for move in candidates_for(board, CENTRE) if move.destination == EAST]


def test_a_gorilla_can_push_a_plain_king(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Push an ordinary King, which is neither a Gorilla nor hovering.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.GORILLA, Color.WHITE)
    board = place(board, EAST, PieceKind.KING, Color.BLACK)

    assert _to(candidates_for(board, CENTRE), EAST).action is MoveAction.PUSH


def test_a_gorilla_cannot_push_a_piece_off_the_board(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Forbid the move entirely when the push would leave the board.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    gorilla = Coordinate(2, 3)
    victim = Coordinate(2, 4)
    board = place(empty_board, gorilla, PieceKind.GORILLA, Color.WHITE)
    board = place(board, victim, PieceKind.PAWN, Color.BLACK)

    assert not [move for move in candidates_for(board, gorilla) if move.destination == victim]


def test_a_catapult_steps_but_never_captures(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Move the Catapult like a King while refusing every capture.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.CATAPULT, Color.WHITE)
    board = place(board, EAST, PieceKind.PAWN, Color.BLACK)

    moves = candidates_for(board, CENTRE)

    assert MoveAction.CAPTURE not in _actions(moves)
    assert not [move for move in moves if move.destination == EAST]


def test_a_catapult_flings_a_friendly_neighbour_past_itself(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Launch the neighbour along the line running through the Catapult.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.CATAPULT, Color.WHITE)
    board = place(board, WEST, PieceKind.PAWN, Color.WHITE)

    flings = [move for move in candidates_for(board, CENTRE) if move.action is MoveAction.FLING]

    assert {move.destination for move in flings} == {EAST, FAR_EAST}
    assert all(move.actor == CENTRE and move.origin == WEST for move in flings)
    assert all(move.is_actor_moving is False for move in flings)


def test_a_flung_piece_flies_over_whatever_is_in_the_way(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Pass over a blocking piece and land beyond it, which a slide cannot do.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.CATAPULT, Color.WHITE)
    board = place(board, WEST, PieceKind.PAWN, Color.WHITE)
    board = place(board, EAST, PieceKind.GORILLA, Color.WHITE)

    flings = [move for move in candidates_for(board, CENTRE) if move.action is MoveAction.FLING]

    assert FAR_EAST in {move.destination for move in flings}


@pytest.mark.parametrize(
    "kind",
    [PieceKind.KING, PieceKind.JET_PACK_KING, PieceKind.GORILLA],
    ids=["king", "jet-pack-king", "gorilla"],
)
def test_a_flung_piece_cannot_capture_a_king_or_gorilla(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    kind: PieceKind,
) -> None:
    """
    Spare a King or Gorilla from a fling capture, Jet Pack King included.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        kind: The protected kind standing on the landing square.
    """
    board = place(empty_board, CENTRE, PieceKind.CATAPULT, Color.WHITE)
    board = place(board, WEST, PieceKind.PAWN, Color.WHITE)
    board = place(board, EAST, kind, Color.BLACK)

    flings = [move for move in candidates_for(board, CENTRE) if move.action is MoveAction.FLING]

    assert EAST not in {move.destination for move in flings}
    assert FAR_EAST in {move.destination for move in flings}


def test_a_catapult_cannot_fling_a_time_machine(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Refuse to launch a Time Machine, which the rules exclude by name.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.CATAPULT, Color.WHITE)
    board = place(board, WEST, PieceKind.TIME_MACHINE, Color.WHITE)

    assert not [move for move in candidates_for(board, CENTRE) if move.action is MoveAction.FLING]


def test_a_catapult_cannot_fling_an_enemy_piece(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Launch only friendly neighbours.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, CENTRE, PieceKind.CATAPULT, Color.WHITE)
    board = place(board, WEST, PieceKind.PAWN, Color.BLACK)

    assert not [move for move in candidates_for(board, CENTRE) if move.action is MoveAction.FLING]


@pytest.mark.parametrize(
    "kind", [PieceKind.GORILLA, PieceKind.CATAPULT], ids=["gorilla", "catapult"]
)
def test_the_new_rules_do_not_mutate_the_board(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    kind: PieceKind,
) -> None:
    """
    Keep generation pure, the invariant the old push and fling both broke.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        kind: The rule under test.
    """
    board = place(empty_board, CENTRE, kind, Color.WHITE)
    board = place(board, WEST, PieceKind.PAWN, Color.WHITE)
    board = place(board, EAST, PieceKind.PAWN, Color.BLACK)
    cells_before = board.cells
    rendered_before = str(board)

    candidates_for(board, CENTRE)

    assert board.cells is cells_before
    assert str(board) == rendered_before
