from dataclasses import FrozenInstanceError

import pytest

from backend.domain.coordinates import (
    ALL_DIRECTIONS,
    DIAGONAL,
    KNIGHT_LEAPS,
    ORTHOGONAL,
    SIDEWAYS,
    Coordinate,
    Offset,
)
from backend.domain.errors import InvalidCoordinateError

# Hoisted because several tables parametrize over the same argument name.
OFFSET_ARG = "offset"


@pytest.mark.parametrize(
    "row,column",
    [
        (-1, 0),
        (0, -1),
        (-1, -1),
        (True, 0),
        (0, True),
        (False, 0),
        (1.0, 0),
        (0, 1.5),
        ("1", 0),
        (0, None),
    ],
    ids=[
        "negative-row",
        "negative-column",
        "both-negative",
        "bool-row-true",
        "bool-column-true",
        "bool-row-false",
        "float-row",
        "float-column",
        "string-row",
        "none-column",
    ],
)
def test_coordinate_rejects_values_that_cannot_name_a_square(row: object, column: object) -> None:
    """
    Reject negatives and non-integers, bool included.

    bool subclasses int, so Coordinate(True, 0) would silently become the
    square at (1, 0) under a plain isinstance check.

    Arguments:
        row: Offending row value.
        column: Offending column value.
    """
    with pytest.raises(InvalidCoordinateError):
        Coordinate(row, column)  # type: ignore[arg-type]


def test_invalid_coordinate_error_reports_the_offending_values() -> None:
    """
    Keep the rejected values on the raised error for diagnostics.
    """
    with pytest.raises(InvalidCoordinateError) as raised:
        Coordinate(-3, 4)

    assert raised.value.row == -3
    assert raised.value.column == 4


@pytest.mark.parametrize("row,column", [(0, 0), (0, 7), (10, 10), (255, 3)])
def test_coordinate_accepts_non_negative_integers(row: int, column: int) -> None:
    """
    Accept any pair of non-negative integers without a bounds opinion.

    Bounds belong to the board, so a coordinate past the edge of the game
    board is still a well-formed coordinate.

    Arguments:
        row: Row index to build with.
        column: Column index to build with.
    """
    square = Coordinate(row, column)

    assert (square.row, square.column) == (row, column)


def test_coordinate_is_frozen() -> None:
    """
    Refuse attribute assignment so a square cannot be edited in place.
    """
    square = Coordinate(1, 1)

    with pytest.raises(FrozenInstanceError):
        square.row = 2  # type: ignore[misc]


def test_coordinate_is_hashable_and_compares_by_value() -> None:
    """
    Behave as a value object, so coordinates can key dicts and fill sets.
    """
    first = Coordinate(2, 3)
    second = Coordinate(2, 3)

    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second, Coordinate(3, 2)}) == 2
    assert {first: "centre"}[second] == "centre"


def test_coordinate_renders_as_row_and_column() -> None:
    """
    Render a square readably for test failure output.
    """
    assert str(Coordinate(4, 9)) == "(4, 9)"


@pytest.mark.parametrize(
    OFFSET_ARG,
    [Offset(-1, 0), Offset(0, -1), Offset(-1, -1), Offset(-2, 1), Offset(1, -2)],
)
def test_shifted_returns_none_when_it_would_leave_the_grid(offset: Offset) -> None:
    """
    Return None instead of raising when a step walks off the low edge.

    Walking off the edge is how a slide terminates, so it is a normal result
    rather than an error.

    Arguments:
        offset: A step that must leave the corner negative.
    """
    assert Coordinate(0, 0).shifted(offset) is None


def test_shifted_returns_none_when_repetition_crosses_zero() -> None:
    """
    Apply times before the negativity check, not after each single step.
    """
    square = Coordinate(1, 1)

    assert square.shifted(Offset(-1, 0)) == Coordinate(0, 1)
    assert square.shifted(Offset(-1, 0), 2) is None


@pytest.mark.parametrize(
    "times,expected",
    [
        (0, Coordinate(2, 2)),
        (1, Coordinate(3, 4)),
        (2, Coordinate(4, 6)),
        (3, Coordinate(5, 8)),
    ],
)
def test_shifted_applies_the_offset_a_given_number_of_times(
    times: int, expected: Coordinate
) -> None:
    """
    Scale a step by a repetition count, which is how a slide walks a ray.

    Arguments:
        times: How many times the offset is applied.
        expected: The square the walk should reach.
    """
    assert Coordinate(2, 2).shifted(Offset(1, 2), times) == expected


@pytest.mark.parametrize(
    "offset,expected",
    [
        (Offset(0, 0), Offset(0, 0)),
        (Offset(2, -1), Offset(-2, 1)),
        (Offset(-1, -1), Offset(1, 1)),
    ],
)
def test_offset_inverted_negates_both_components(offset: Offset, expected: Offset) -> None:
    """
    Reverse a direction, which is what the Catapult flings along.

    Arguments:
        offset: The direction to reverse.
        expected: The reversed direction.
    """
    assert offset.inverted == expected


@pytest.mark.parametrize(OFFSET_ARG, ALL_DIRECTIONS + KNIGHT_LEAPS)
def test_inverting_twice_gives_the_original_direction(offset: Offset) -> None:
    """
    Make inversion an involution for every direction the engine uses.

    Arguments:
        offset: A direction from the shared tables.
    """
    assert offset.inverted.inverted == offset


@pytest.mark.parametrize(OFFSET_ARG, ALL_DIRECTIONS)
def test_every_direction_is_an_adjacent_step(offset: Offset) -> None:
    """
    Treat all eight king directions as touching squares.

    Arguments:
        offset: One of the eight compass directions.
    """
    assert offset.is_adjacent_step is True


@pytest.mark.parametrize(OFFSET_ARG, KNIGHT_LEAPS)
def test_no_knight_leap_is_an_adjacent_step(offset: Offset) -> None:
    """
    Keep every knight leap outside the touching ring.

    Arguments:
        offset: One of the eight knight offsets.
    """
    assert offset.is_adjacent_step is False


def test_zero_offset_counts_as_adjacent() -> None:
    """
    Treat the null step as adjacent, since Chebyshev distance zero is inside
    the touching ring.
    """
    assert Offset(0, 0).is_adjacent_step is True


def test_direction_tables_are_distinct_and_consistent() -> None:
    """
    Keep the shared offset tables free of duplicates and overlap.

    These tables replaced per-piece copies of the same literals, so a mistake
    here would reach every piece at once.
    """
    assert len(set(ORTHOGONAL)) == len(ORTHOGONAL) == 4
    assert len(set(DIAGONAL)) == len(DIAGONAL) == 4
    assert set(ALL_DIRECTIONS) == set(ORTHOGONAL) | set(DIAGONAL)
    assert len(set(ALL_DIRECTIONS)) == 8
    assert len(set(KNIGHT_LEAPS)) == 8
    assert set(ALL_DIRECTIONS).isdisjoint(KNIGHT_LEAPS)
    assert set(SIDEWAYS) < set(ORTHOGONAL)
