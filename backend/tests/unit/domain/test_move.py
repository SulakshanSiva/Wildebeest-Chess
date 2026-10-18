from collections.abc import Callable

import pytest

from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, MoveAction, PieceKind
from backend.domain.move import Displacement, Move, MoveRecord

ORIGIN = Coordinate(4, 4)
DESTINATION = Coordinate(4, 5)
BEYOND = Coordinate(4, 6)
CATAPULT = Coordinate(3, 4)

# The same four moves are tabled three times over, by the factories below.
BUILDER_CASES = "builder,expected"
BUILDER_IDS = ["move", "capture", "push", "fling"]


def _quiet_move() -> Move:
    """
    Build a plain move onto an empty square.

    Returns:
        A MOVE whose actor is the piece that travels.
    """
    return Move.simple(ORIGIN, DESTINATION, capture=False)


def _capture_move() -> Move:
    """
    Build a move onto an enemy-occupied square.

    Returns:
        A CAPTURE whose actor is the piece that travels.
    """
    return Move.simple(ORIGIN, DESTINATION, capture=True)


def _push_move() -> Move:
    """
    Build a Gorilla step that shoves the occupant one square further.

    Returns:
        A PUSH carrying a displacement.
    """
    return Move.push(ORIGIN, DESTINATION, BEYOND)


def _fling_move() -> Move:
    """
    Build a Catapult launch, in which the catapult stays put.

    Returns:
        A FLING whose actor differs from its origin.
    """
    return Move.fling(CATAPULT, ORIGIN, BEYOND)


@pytest.mark.parametrize(
    "capture,expected",
    [(False, MoveAction.MOVE), (True, MoveAction.CAPTURE)],
    ids=["quiet", "capture"],
)
def test_simple_puts_the_mover_at_both_actor_and_origin(
    capture: bool, expected: MoveAction
) -> None:
    """
    Describe an ordinary move, where the piece spending the turn is the piece
    that travels.

    Arguments:
        capture: Whether an enemy occupies the destination.
        expected: The action the move should carry.
    """
    move = Move.simple(ORIGIN, DESTINATION, capture=capture)

    assert move.actor == ORIGIN
    assert move.origin == ORIGIN
    assert move.destination == DESTINATION
    assert move.action is expected
    assert move.displaced is None


def test_push_records_the_shoved_occupant() -> None:
    """
    Describe a Gorilla step as a move plus a secondary displacement, so the
    applier knows which piece went where.
    """
    move = _push_move()

    assert move.actor == ORIGIN
    assert move.origin == ORIGIN
    assert move.destination == DESTINATION
    assert move.action is MoveAction.PUSH
    assert move.displaced == Displacement(origin=DESTINATION, destination=BEYOND)


def test_fling_separates_the_actor_from_the_piece_that_moves() -> None:
    """
    Describe a Catapult launch with three squares, which the prototype's
    isFlung boolean could not express.
    """
    move = _fling_move()

    assert move.actor == CATAPULT
    assert move.origin == ORIGIN
    assert move.destination == BEYOND
    assert move.action is MoveAction.FLING
    assert move.displaced is None


@pytest.mark.parametrize(
    BUILDER_CASES,
    [
        (_quiet_move, True),
        (_capture_move, True),
        (_push_move, True),
        (_fling_move, False),
    ],
    ids=BUILDER_IDS,
)
def test_is_actor_moving_is_false_only_for_a_fling(
    builder: Callable[[], Move], expected: bool
) -> None:
    """
    Report whether the piece spending the turn is the piece that travels.

    Arguments:
        builder: Factory for the move under test.
        expected: Whether the actor is the travelling piece.
    """
    assert builder().is_actor_moving is expected


@pytest.mark.parametrize(
    BUILDER_CASES,
    [
        (_quiet_move, "MOVE (4, 4)->(4, 5)"),
        (_capture_move, "CAPTURE (4, 4)->(4, 5)"),
        (_push_move, "PUSH (4, 4)->(4, 5)"),
        (_fling_move, "FLING by (3, 4) (4, 4)->(4, 6)"),
    ],
    ids=BUILDER_IDS,
)
def test_move_renders_the_actor_only_when_it_differs(
    builder: Callable[[], Move], expected: str
) -> None:
    """
    Render a move for test output, naming the actor only for a fling.

    Arguments:
        builder: Factory for the move under test.
        expected: The expected rendering.
    """
    assert str(builder()) == expected


def test_moves_compare_by_value() -> None:
    """
    Treat moves as value objects, which candidate deduplication relies on.
    """
    assert _quiet_move() == Move.simple(ORIGIN, DESTINATION, capture=False)
    assert _quiet_move() != _capture_move()
    assert len({_quiet_move(), Move.simple(ORIGIN, DESTINATION, capture=False)}) == 1


def test_move_record_defaults_to_no_captures_at_the_first_ply() -> None:
    """
    Record an applied move with what it removed, so it can be undone later.
    """
    record = MoveRecord(move=_quiet_move(), moved_piece_id=3, side=Color.WHITE)

    assert record.captured == ()
    assert record.ply == 0


def test_move_record_remembers_captured_pieces_by_identity() -> None:
    """
    Store captures as id and kind rather than live pieces, so a record stays
    valid once the board has moved on.
    """
    record = MoveRecord(
        move=_capture_move(),
        moved_piece_id=3,
        side=Color.BLACK,
        captured=((9, PieceKind.GORILLA),),
        ply=7,
    )

    assert record.captured == ((9, PieceKind.GORILLA),)
    assert record.ply == 7
