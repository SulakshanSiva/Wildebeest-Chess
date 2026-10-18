from collections.abc import Callable, Iterable

import pytest

from backend.domain.board import Board
from backend.domain.coordinates import (
    ALL_DIRECTIONS,
    DIAGONAL,
    KNIGHT_LEAPS,
    ORTHOGONAL,
    Coordinate,
    Offset,
)
from backend.domain.enums import Color, MoveAction, PieceKind
from backend.domain.errors import SquareEmptyError
from backend.domain.move import Move
from backend.domain.pieces.base import MovementRule
from backend.domain.pieces.movement import (
    CompositeRule,
    LeapRule,
    NoMovementRule,
    PawnRule,
    SlideRule,
    step_rule,
)
from backend.domain.pieces.registry import create_piece


def _squares(pairs: Iterable[tuple[int, int]]) -> set[Coordinate]:
    """
    Turn row and column pairs into a set of coordinates.

    Arguments:
        pairs: Row and column pairs naming the squares.

    Returns:
        The squares as a set, ready to compare against generated destinations.
    """
    return {Coordinate(row, column) for row, column in pairs}


def _action_at(moves: Iterable[Move], square: Coordinate) -> MoveAction:
    """
    Give the action of the one move that lands on a square.

    Arguments:
        moves: The candidate moves to search.
        square: The destination to look for.

    Returns:
        The action of the matching move.
    """
    return next(move.action for move in moves if move.destination == square)


# Every expected set below is written out as literal squares on the 5x5
# fixture board, so a wrong offset table cannot quietly agree with itself.
KNIGHT_FROM_CENTRE = _squares(((0, 1), (0, 3), (1, 0), (1, 4), (3, 0), (3, 4), (4, 1), (4, 3)))
ADJACENT_TO_CENTRE = _squares(((1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2), (3, 3)))
ORTHOGONAL_FROM_CENTRE = _squares(((0, 2), (1, 2), (3, 2), (4, 2), (2, 0), (2, 1), (2, 3), (2, 4)))
DIAGONAL_FROM_CENTRE = _squares(((0, 0), (1, 1), (3, 3), (4, 4), (0, 4), (1, 3), (3, 1), (4, 0)))
QUEEN_FROM_CENTRE = ORTHOGONAL_FROM_CENTRE | DIAGONAL_FROM_CENTRE
SIDEWAYS_FROM_CENTRE = _squares(((2, 1), (2, 3)))

BLOCKER = PieceKind.ROOK
NEAR_EAST = Coordinate(2, 3)
FAR_EAST = Coordinate(2, 4)
KNIGHT_TARGET = Coordinate(4, 3)

WHITE_PAWN_HOME = Coordinate(1, 2)
BLACK_PAWN_HOME = Coordinate(3, 2)
PAWN_STEP = Coordinate(2, 2)


@pytest.mark.parametrize(
    "kind,expected",
    [
        (PieceKind.KNIGHT, KNIGHT_FROM_CENTRE),
        (PieceKind.ROOK, ORTHOGONAL_FROM_CENTRE),
        (PieceKind.BISHOP, DIAGONAL_FROM_CENTRE),
        (PieceKind.JET_PACK_KING, DIAGONAL_FROM_CENTRE),
        (PieceKind.KING, ADJACENT_TO_CENTRE),
        (PieceKind.JOEY, ADJACENT_TO_CENTRE),
        (PieceKind.OLD_WOMAN, ADJACENT_TO_CENTRE),
        (PieceKind.BEEKEEPER, ADJACENT_TO_CENTRE),
        (PieceKind.SERPENT, ADJACENT_TO_CENTRE),
        (PieceKind.GRAND_EMPRESS, QUEEN_FROM_CENTRE | KNIGHT_FROM_CENTRE),
        (PieceKind.TIME_MACHINE, set()),
    ],
)
def test_each_specified_piece_reaches_its_own_squares_from_an_open_centre(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
    kind: PieceKind,
    expected: set[Coordinate],
) -> None:
    """
    Pin the movement contract of every piece whose rules are decided.

    The pawn is absent because its reach depends on colour and first move; it
    has its own table below. The Gorilla and Catapult are absent because their
    rules are still open.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: The square the piece stands on.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
        kind: The piece kind under test.
        expected: The squares it should be able to reach.
    """
    board = place(empty_board, centre, kind, Color.WHITE)

    assert destinations(candidates_for(board, centre)) == expected


@pytest.mark.parametrize(
    "corner,expected",
    [
        (Coordinate(0, 0), ((1, 2), (2, 1))),
        (Coordinate(0, 4), ((1, 2), (2, 3))),
        (Coordinate(4, 0), ((2, 1), (3, 2))),
        (Coordinate(4, 4), ((2, 3), (3, 2))),
    ],
    ids=["top-left", "top-right", "bottom-left", "bottom-right"],
)
def test_a_leap_is_clipped_to_the_board(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
    corner: Coordinate,
    expected: tuple[tuple[int, int], ...],
) -> None:
    """
    Drop the leaps that would land off the grid, in both directions.

    Negative targets are refused by Coordinate.shifted and oversized ones by
    the board, so a corner exercises both guards at once.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
        corner: Corner square the knight stands on.
        expected: The only two squares it can reach from there.
    """
    board = place(empty_board, corner, PieceKind.KNIGHT, Color.WHITE)

    assert destinations(candidates_for(board, corner)) == _squares(expected)


def test_a_leap_is_blocked_by_a_friendly_piece(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
) -> None:
    """
    Refuse a landing square held by the leaper's own side.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the knight stands on.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
    """
    board = place(empty_board, centre, PieceKind.KNIGHT, Color.WHITE)
    board = place(board, KNIGHT_TARGET, BLOCKER, Color.WHITE)

    moves = candidates_for(board, centre)

    assert destinations(moves) == KNIGHT_FROM_CENTRE - {KNIGHT_TARGET}
    assert all(move.action is MoveAction.MOVE for move in moves)


def test_a_leap_captures_an_enemy_on_its_landing_square(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
) -> None:
    """
    Keep a landing square held by the other side, marked as a capture.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the knight stands on.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
    """
    board = place(empty_board, centre, PieceKind.KNIGHT, Color.WHITE)
    board = place(board, KNIGHT_TARGET, BLOCKER, Color.BLACK)

    moves = candidates_for(board, centre)

    assert destinations(moves) == KNIGHT_FROM_CENTRE
    assert _action_at(moves, KNIGHT_TARGET) is MoveAction.CAPTURE


@pytest.mark.parametrize("occupant", [Color.WHITE, Color.BLACK], ids=["friendly", "enemy"])
def test_a_serpent_generates_no_capture_at_all(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
    occupant: Color,
) -> None:
    """
    Treat every occupied neighbour as blocked, whichever side holds it.

    The Serpent has no capture branch in the prototype, so can_capture is
    False and an adjacent enemy must not become a target.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the serpent stands on.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
        occupant: Colour of the adjacent piece.
    """
    board = place(empty_board, centre, PieceKind.SERPENT, Color.WHITE)
    board = place(board, NEAR_EAST, BLOCKER, occupant)

    moves = candidates_for(board, centre)

    assert destinations(moves) == ADJACENT_TO_CENTRE - {NEAR_EAST}
    assert all(move.action is MoveAction.MOVE for move in moves)


def test_step_rule_builds_a_single_square_leap() -> None:
    """
    Keep step_rule a naming convenience over LeapRule rather than a new class.
    """
    assert step_rule(ALL_DIRECTIONS) == LeapRule(offsets=ALL_DIRECTIONS, can_capture=True)
    assert step_rule(ALL_DIRECTIONS, can_capture=False).can_capture is False


def test_a_slide_stops_before_a_friendly_piece(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
) -> None:
    """
    End a ray one square short of the slider's own piece, reaching nothing
    behind it.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the rook stands on.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
    """
    board = place(empty_board, centre, PieceKind.ROOK, Color.WHITE)
    board = place(board, NEAR_EAST, BLOCKER, Color.WHITE)

    moves = candidates_for(board, centre)

    assert destinations(moves) == ORTHOGONAL_FROM_CENTRE - {NEAR_EAST, FAR_EAST}


def test_a_slide_stops_on_an_enemy_and_takes_it(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
) -> None:
    """
    End a ray on the enemy it meets, including that square as a capture and
    nothing beyond it.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the rook stands on.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
    """
    board = place(empty_board, centre, PieceKind.ROOK, Color.WHITE)
    board = place(board, NEAR_EAST, BLOCKER, Color.BLACK)

    moves = candidates_for(board, centre)

    assert destinations(moves) == ORTHOGONAL_FROM_CENTRE - {FAR_EAST}
    assert _action_at(moves, NEAR_EAST) is MoveAction.CAPTURE


@pytest.mark.parametrize(
    "directions,max_distance,expected",
    [
        (ORTHOGONAL, 1, _squares(((1, 2), (3, 2), (2, 1), (2, 3)))),
        (ORTHOGONAL, 2, ORTHOGONAL_FROM_CENTRE),
        (ALL_DIRECTIONS, 1, ADJACENT_TO_CENTRE),
        (ALL_DIRECTIONS, None, QUEEN_FROM_CENTRE),
    ],
    ids=["one-step", "two-steps", "all-directions-one-step", "unlimited"],
)
def test_max_distance_limits_how_far_a_slide_reaches(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
    directions: tuple[Offset, ...],
    max_distance: int | None,
    expected: set[Coordinate],
) -> None:
    """
    Cap a slider's reach, and run to the edge when no cap is configured.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the slider stands on.
        place: Helper that builds and places a piece.
        destinations: Helper reducing moves to squares.
        directions: Directions the rule slides along.
        max_distance: Configured reach, or None for unlimited.
        expected: The squares it should reach.
    """
    board = place(empty_board, centre, PieceKind.ROOK, Color.WHITE)
    rule = SlideRule(directions=directions, max_distance=max_distance)

    assert destinations(rule.candidates(board, centre)) == expected


@pytest.mark.parametrize(
    "color,origin,has_moved,occupants,expected",
    [
        (Color.WHITE, WHITE_PAWN_HOME, False, (), ((2, 2), (3, 2))),
        (Color.BLACK, BLACK_PAWN_HOME, False, (), ((2, 2), (1, 2))),
        (Color.WHITE, WHITE_PAWN_HOME, True, (), ((2, 2),)),
        (Color.BLACK, BLACK_PAWN_HOME, True, (), ((2, 2),)),
        (Color.WHITE, WHITE_PAWN_HOME, False, ((PAWN_STEP, Color.WHITE),), ()),
        (Color.WHITE, WHITE_PAWN_HOME, False, ((PAWN_STEP, Color.BLACK),), ()),
        (Color.WHITE, WHITE_PAWN_HOME, False, ((Coordinate(3, 2), Color.WHITE),), ((2, 2),)),
        (
            Color.WHITE,
            WHITE_PAWN_HOME,
            False,
            ((Coordinate(2, 1), Color.BLACK), (Coordinate(2, 3), Color.WHITE)),
            ((2, 2), (3, 2), (2, 1)),
        ),
        (
            Color.WHITE,
            WHITE_PAWN_HOME,
            False,
            ((Coordinate(2, 1), Color.BLACK), (Coordinate(2, 3), Color.BLACK)),
            ((2, 2), (3, 2), (2, 1), (2, 3)),
        ),
        (
            Color.WHITE,
            WHITE_PAWN_HOME,
            False,
            (
                (Coordinate(2, 1), Color.WHITE),
                (PAWN_STEP, Color.WHITE),
                (Coordinate(2, 3), Color.WHITE),
            ),
            (),
        ),
        (Color.WHITE, Coordinate(4, 2), False, (), ()),
        (Color.BLACK, Coordinate(0, 2), False, (), ()),
    ],
    ids=[
        "white-advances-up",
        "black-advances-down",
        "white-after-first-move",
        "black-after-first-move",
        "near-square-blocked-by-friend",
        "near-square-blocked-by-enemy",
        "far-square-blocked",
        "one-diagonal-enemy-one-friend",
        "both-diagonals-enemy",
        "fully-blocked",
        "white-facing-the-edge",
        "black-facing-the-edge",
    ],
)
def test_pawn_movement_contract(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
    color: Color,
    origin: Coordinate,
    has_moved: bool,
    occupants: tuple[tuple[Coordinate, Color], ...],
    expected: tuple[tuple[int, int], ...],
) -> None:
    """
    Pin pawn direction, the first-move double step, and blocked advances.

    The two blocked-near-square cases are the important ones: the double step
    is nested inside the single step, so a blocked first square must cancel
    both even though the far square is empty.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
        color: Colour of the pawn.
        origin: Square the pawn stands on.
        has_moved: Whether the pawn has already moved.
        occupants: Other pieces to place, as square and colour.
        expected: The squares the pawn should reach.
    """
    board = place(empty_board, origin, PieceKind.PAWN, color, has_moved=has_moved)
    for square, occupant_color in occupants:
        board = place(board, square, BLOCKER, occupant_color)

    assert destinations(candidates_for(board, origin)) == _squares(expected)


def test_a_pawn_cannot_capture_straight_ahead(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Generate no capture against the piece directly in front of a pawn.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, WHITE_PAWN_HOME, PieceKind.PAWN, Color.WHITE)
    board = place(board, PAWN_STEP, BLOCKER, Color.BLACK)

    moves = candidates_for(board, WHITE_PAWN_HOME)

    assert moves == ()


def test_a_pawn_marks_its_diagonal_capture_as_a_capture(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Record the action of a diagonal take, not merely its destination.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    target = Coordinate(2, 1)
    board = place(empty_board, WHITE_PAWN_HOME, PieceKind.PAWN, Color.WHITE)
    board = place(board, target, BLOCKER, Color.BLACK)

    moves = candidates_for(board, WHITE_PAWN_HOME)

    assert _action_at(moves, target) is MoveAction.CAPTURE
    assert _action_at(moves, PAWN_STEP) is MoveAction.MOVE


def test_an_immobile_piece_offers_no_moves(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
) -> None:
    """
    Return nothing for a piece that cannot move, even next to an enemy.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the Time Machine stands on.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
    """
    board = place(empty_board, centre, PieceKind.TIME_MACHINE, Color.WHITE)
    board = place(board, NEAR_EAST, BLOCKER, Color.BLACK)

    assert candidates_for(board, centre) == ()


def test_immobility_is_a_stated_reason_rather_than_an_empty_override() -> None:
    """
    Expose why a piece cannot move, so metadata can explain it.
    """
    rule = NoMovementRule(reason="the Time Machine cannot move or capture")

    assert rule.description == "the Time Machine cannot move or capture"


def test_a_composite_reaches_the_union_of_its_components(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
) -> None:
    """
    Combine a knight leap and a queen slide without losing either.

    Composition rather than inheritance is what lets the Grand Empress hold
    two mechanisms at once.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the Grand Empress stands on.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
    """
    board = place(empty_board, centre, PieceKind.GRAND_EMPRESS, Color.WHITE)

    leap = LeapRule(offsets=KNIGHT_LEAPS).candidates(board, centre)
    slide = SlideRule(directions=ALL_DIRECTIONS).candidates(board, centre)
    combined = candidates_for(board, centre)

    assert destinations(combined) == destinations(leap) | destinations(slide)
    assert len(combined) == len(leap) + len(slide)


def test_a_composite_drops_moves_two_components_both_reach(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
) -> None:
    """
    Keep one move per square when components overlap, since two routes to the
    same square are still one move.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the piece stands on.
        place: Helper that builds and places a piece.
        destinations: Helper reducing moves to squares.
    """
    board = place(empty_board, centre, PieceKind.KNIGHT, Color.WHITE)
    overlapping = CompositeRule(
        rules=(LeapRule(offsets=KNIGHT_LEAPS), LeapRule(offsets=KNIGHT_LEAPS))
    )
    orthogonal_and_diagonal = CompositeRule(
        rules=(SlideRule(directions=ORTHOGONAL), SlideRule(directions=DIAGONAL))
    )

    duplicated = overlapping.candidates(board, centre)

    assert len(duplicated) == len(KNIGHT_FROM_CENTRE)
    assert destinations(duplicated) == KNIGHT_FROM_CENTRE
    assert destinations(orthogonal_and_diagonal.candidates(board, centre)) == QUEEN_FROM_CENTRE


@pytest.mark.parametrize(
    "rule",
    [
        LeapRule(offsets=KNIGHT_LEAPS),
        SlideRule(directions=ORTHOGONAL),
        PawnRule(),
        NoMovementRule(),
        CompositeRule(rules=(PawnRule(),)),
    ],
    ids=["leap", "slide", "pawn", "immobile", "composite"],
)
def test_every_rule_refuses_an_origin_with_no_piece_on_it(
    empty_board: Board, centre: Coordinate, rule: MovementRule
) -> None:
    """
    Reject a caller that names a square its piece is not standing on.

    The rule contract takes a board and a square rather than a piece, so this
    is the check that keeps the two from disagreeing.

    Arguments:
        empty_board: A board with nothing on it.
        centre: The empty square being asked about.
        rule: The rule under test.
    """
    with pytest.raises(SquareEmptyError):
        rule.candidates(empty_board, centre)


@pytest.mark.parametrize("kind", list(PieceKind), ids=[kind.value for kind in PieceKind])
def test_generating_candidates_never_changes_the_board(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    kind: PieceKind,
) -> None:
    """
    Hold the purity contract for every rule type, undecided ones included.

    The prototype's Gorilla and Catapult wrote to the board while generating
    moves, so merely asking what a piece could do could alter the game. The
    board is compared both by rendering and cell for cell, and neighbours of
    both colours are present so capture and push branches are reached.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the piece stands on.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        kind: The piece kind whose rule is exercised.
    """
    board = place(empty_board, centre, kind, Color.WHITE)
    board = place(board, NEAR_EAST, BLOCKER, Color.BLACK)
    board = place(board, Coordinate(3, 3), BLOCKER, Color.BLACK)
    board = place(board, Coordinate(1, 1), BLOCKER, Color.WHITE)

    cells_before = board.cells
    rendered_before = str(board)

    candidates_for(board, centre)

    assert board.cells is cells_before
    assert str(board) == rendered_before
    board.validate()


@pytest.mark.parametrize("kind", list(PieceKind), ids=[kind.value for kind in PieceKind])
def test_candidate_moves_always_start_from_the_square_asked_about(
    empty_board: Board,
    centre: Coordinate,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    kind: PieceKind,
) -> None:
    """
    Keep every generated move anchored to the origin, in bounds, and off the
    square it started on.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        centre: Square the piece stands on.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        kind: The piece kind whose rule is exercised.
    """
    board = place(empty_board, centre, kind, Color.WHITE)
    board = place(board, NEAR_EAST, BLOCKER, Color.BLACK)

    moves = candidates_for(board, centre)

    for move in moves:
        assert move.origin == centre
        assert move.actor == centre
        assert move.destination != centre
        assert board.contains(move.destination) is True


def test_a_create_piece_helper_attaches_the_registered_rule() -> None:
    """
    Give each piece its own rule instance, so per-piece configuration stays
    possible later.
    """
    first = create_piece(piece_id=1, kind=PieceKind.KNIGHT, color=Color.WHITE)
    second = create_piece(piece_id=2, kind=PieceKind.KNIGHT, color=Color.BLACK)

    assert isinstance(first.movement, LeapRule)
    assert first.movement == second.movement
    assert first.has_moved is False


def test_a_golf_cart_moves_sideways_on_an_edge_row(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
) -> None:
    """
    Let the Golf Cart step left and right while it is on the top or bottom row.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
    """
    origin = Coordinate(0, 2)
    board = place(empty_board, origin, PieceKind.GOLF_CART, Color.WHITE)

    assert destinations(candidates_for(board, origin)) == {Coordinate(0, 1), Coordinate(0, 3)}


def test_a_golf_cart_on_the_bottom_row_also_moves(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    destinations: Callable[[Iterable[Move]], set[Coordinate]],
) -> None:
    """
    Treat the last row as an edge row too, not only row zero.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        destinations: Helper reducing moves to squares.
    """
    origin = Coordinate(4, 2)
    board = place(empty_board, origin, PieceKind.GOLF_CART, Color.WHITE)

    assert destinations(candidates_for(board, origin)) == {Coordinate(4, 1), Coordinate(4, 3)}


@pytest.mark.parametrize("row", [1, 2, 3], ids=["row-1", "middle", "row-3"])
def test_a_displaced_golf_cart_cannot_move(
    empty_board: Board,
    place: Callable[..., Board],
    candidates_for: Callable[[Board, Coordinate], tuple[Move, ...]],
    row: int,
) -> None:
    """
    Immobilise a Golf Cart knocked off an edge row by a push or a fling.

    The rules restrict it to moving "left and right in the bottom and top
    rows", so a cart anywhere else has no legal move of its own.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        candidates_for: Helper that asks a piece for its candidates.
        row: The non-edge row to place the cart on.
    """
    origin = Coordinate(row, 2)
    board = place(empty_board, origin, PieceKind.GOLF_CART, Color.WHITE)

    assert candidates_for(board, origin) == ()
