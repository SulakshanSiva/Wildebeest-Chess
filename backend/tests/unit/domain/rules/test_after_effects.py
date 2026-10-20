from __future__ import annotations

from collections.abc import Callable

import pytest

from backend.domain.board import Board, BoardDimensions
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, GameStatus, PieceKind, RemovalCause
from backend.domain.move import Transport
from backend.domain.pieces.registry import create_piece
from backend.domain.rules.after_effects import (
    apply_golf_cart_rampage,
    apply_joey_explosions,
    apply_poisoning,
    apply_promotion,
    run_after_effects,
)
from backend.domain.rules.outcome import evaluate_status, surviving_royals
from backend.domain.rules.paralysis import is_paralysed
from backend.domain.variant import WILDEBEEST_TRANSPORTER_LINKS, Variant


@pytest.fixture
def wide_board() -> Board:
    """
    Give an empty 11x11 board, matching the real board's dimensions.

    Returns:
        A board with no pieces and no special terrain.
    """
    return Board.empty(BoardDimensions(11, 11))


def test_a_serpent_poisons_adjacent_enemies_only(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Remove opposing neighbours of a Serpent and spare friendly ones.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.SERPENT, Color.WHITE)
    board = place(board, Coordinate(2, 3), PieceKind.PAWN, Color.BLACK)
    board = place(board, Coordinate(2, 1), PieceKind.PAWN, Color.WHITE)

    result, removed, _ = apply_poisoning(board)

    assert result.piece_at(Coordinate(2, 3)) is None
    assert result.piece_at(Coordinate(2, 1)) is not None
    assert [kind for _, kind in removed] == [PieceKind.PAWN]


def test_a_serpent_can_poison_a_gorilla(empty_board: Board, place: Callable[..., Board]) -> None:
    """
    Kill a Gorilla by poison, the one route past "cannot be captured".

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.SERPENT, Color.WHITE)
    board = place(board, Coordinate(2, 3), PieceKind.GORILLA, Color.BLACK)

    result, _, _ = apply_poisoning(board)

    assert result.piece_at(Coordinate(2, 3)) is None


@pytest.mark.parametrize(
    "kind", [PieceKind.GOLF_CART, PieceKind.TIME_MACHINE], ids=["golf-cart", "time-machine"]
)
def test_some_pieces_cannot_be_poisoned(
    empty_board: Board, place: Callable[..., Board], kind: PieceKind
) -> None:
    """
    Spare the Golf Cart and Time Machine, which the rules make immune.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        kind: The immune kind under test.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.SERPENT, Color.WHITE)
    board = place(board, Coordinate(2, 3), kind, Color.BLACK)

    result, removed, _ = apply_poisoning(board)

    assert result.piece_at(Coordinate(2, 3)) is not None
    assert removed == []


def test_a_grand_empress_poisons_like_a_serpent(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Give the Grand Empress the Serpent's poison, as clarified.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.GRAND_EMPRESS, Color.WHITE)
    board = place(board, Coordinate(2, 3), PieceKind.PAWN, Color.BLACK)

    result, _, _ = apply_poisoning(board)

    assert result.piece_at(Coordinate(2, 3)) is None


def test_an_old_woman_shields_a_neighbour_and_promotes(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Reverse a poisoning: the victim lives, the Serpent dies, she promotes.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    serpent = Coordinate(2, 2)
    victim = Coordinate(2, 3)
    old_woman = Coordinate(2, 4)

    board = place(empty_board, serpent, PieceKind.SERPENT, Color.WHITE)
    board = place(board, victim, PieceKind.PAWN, Color.BLACK)
    board = place(board, old_woman, PieceKind.OLD_WOMAN, Color.BLACK)

    result, _, promoted = apply_poisoning(board)

    assert result.piece_at(victim) is not None
    assert result.piece_at(serpent) is None
    assert result.require_piece_at(old_woman).kind is PieceKind.GRAND_EMPRESS
    assert [kind for _, kind in promoted] == [PieceKind.GRAND_EMPRESS]


def test_an_old_woman_cannot_shield_herself(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Remove an Old Woman poisoned directly; she does not promote.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.SERPENT, Color.WHITE)
    board = place(board, Coordinate(2, 3), PieceKind.OLD_WOMAN, Color.BLACK)

    result, _, promoted = apply_poisoning(board)

    assert result.piece_at(Coordinate(2, 3)) is None
    assert result.piece_at(Coordinate(2, 2)) is not None
    assert promoted == []


@pytest.mark.parametrize(
    "colour,row", [(Color.WHITE, 10), (Color.BLACK, 0)], ids=["white", "black"]
)
def test_a_pawn_reaching_the_far_end_becomes_a_time_machine(
    wide_board: Board, place: Callable[..., Board], colour: Color, row: int
) -> None:
    """
    Promote a pawn to a Time Machine, which is where that piece comes from.

    Arguments:
        wide_board: An empty 11x11 board.
        place: Helper that builds and places a piece.
        colour: Which side's pawn is promoting.
        row: The far row for that colour.
    """
    square = Coordinate(row, 4)
    board = place(wide_board, square, PieceKind.PAWN, colour)

    result, promoted = apply_promotion(board)

    assert result.require_piece_at(square).kind is PieceKind.TIME_MACHINE
    assert [kind for _, kind in promoted] == [PieceKind.TIME_MACHINE]


def test_a_king_on_the_jet_pack_is_promoted_by_the_pipeline(
    place: Callable[..., Board],
) -> None:
    """
    Upgrade a King standing on the real board's jet pack square.

    Arguments:
        place: Helper that builds and places a piece.
    """
    board = Variant().build_board()
    jet_pack = Coordinate(5, 5)
    board = place(board, jet_pack, PieceKind.KING, Color.WHITE)

    result, promoted = apply_promotion(board)

    assert result.require_piece_at(jet_pack).kind is PieceKind.JET_PACK_KING
    assert [kind for _, kind in promoted] == [PieceKind.JET_PACK_KING]


def test_a_time_machine_charges_its_own_sides_cart(
    wide_board: Board, place: Callable[..., Board]
) -> None:
    """
    Send a charged cart down its column, clearing everything on the way.

    Arguments:
        wide_board: An empty 11x11 board.
        place: Helper that builds and places a piece.
    """
    board = place(wide_board, Coordinate(0, 3), PieceKind.GOLF_CART, Color.WHITE)
    board = place(board, Coordinate(4, 3), PieceKind.PAWN, Color.BLACK)
    board = place(board, Coordinate(7, 3), PieceKind.GORILLA, Color.WHITE)
    board = place(board, Coordinate(2, 8), PieceKind.TIME_MACHINE, Color.WHITE)

    result, removed = apply_golf_cart_rampage(board)

    assert result.piece_at(Coordinate(4, 3)) is None
    assert result.piece_at(Coordinate(7, 3)) is None
    assert result.require_piece_at(Coordinate(10, 3)).kind is PieceKind.GOLF_CART
    assert len(removed) == 2


def test_a_pawn_on_the_middle_row_charges_the_opposing_cart(
    wide_board: Board, place: Callable[..., Board]
) -> None:
    """
    Charge the other side's cart when a pawn reaches the middle row.

    Arguments:
        wide_board: An empty 11x11 board.
        place: Helper that builds and places a piece.
    """
    board = place(wide_board, Coordinate(5, 2), PieceKind.PAWN, Color.WHITE)
    board = place(board, Coordinate(0, 7), PieceKind.GOLF_CART, Color.BLACK)
    board = place(board, Coordinate(0, 1), PieceKind.GOLF_CART, Color.WHITE)

    result, _ = apply_golf_cart_rampage(board)

    assert result.piece_at(Coordinate(0, 7)) is None
    assert result.require_piece_at(Coordinate(10, 7)).kind is PieceKind.GOLF_CART
    assert result.require_piece_at(Coordinate(0, 1)).kind is PieceKind.GOLF_CART


def test_two_charged_carts_in_one_column_clear_it_entirely(
    wide_board: Board, place: Callable[..., Board]
) -> None:
    """
    Remove everything in a column holding two charged carts, carts included.

    Arguments:
        wide_board: An empty 11x11 board.
        place: Helper that builds and places a piece.
    """
    board = place(wide_board, Coordinate(0, 4), PieceKind.GOLF_CART, Color.WHITE)
    board = place(board, Coordinate(10, 4), PieceKind.GOLF_CART, Color.BLACK)
    board = place(board, Coordinate(5, 4), PieceKind.ROOK, Color.WHITE)
    board = place(board, Coordinate(3, 9), PieceKind.TIME_MACHINE, Color.WHITE)
    board = place(board, Coordinate(4, 9), PieceKind.TIME_MACHINE, Color.BLACK)

    result, _ = apply_golf_cart_rampage(board)

    assert [square for square, _ in result.pieces() if square.column == 4] == []


def test_a_joey_explodes_when_his_row_holds_a_multiple_of_five(
    wide_board: Board, place: Callable[..., Board]
) -> None:
    """
    Detonate Joey and his neighbours when the row count divides by five.

    Arguments:
        wide_board: An empty 11x11 board.
        place: Helper that builds and places a piece.
    """
    joey = Coordinate(4, 4)
    board = place(wide_board, joey, PieceKind.JOEY, Color.WHITE)
    for column in (0, 1, 2, 5):
        board = place(board, Coordinate(4, column), PieceKind.PAWN, Color.BLACK)
    neighbour = Coordinate(3, 4)
    board = place(board, neighbour, PieceKind.ROOK, Color.WHITE)

    result, removed = apply_joey_explosions(board)

    assert result.piece_at(joey) is None
    assert result.piece_at(Coordinate(4, 5)) is None
    assert result.piece_at(neighbour) is None
    assert result.piece_at(Coordinate(4, 0)) is not None
    assert len(removed) == 3


def test_a_joey_in_a_safe_row_does_not_explode(
    wide_board: Board, place: Callable[..., Board]
) -> None:
    """
    Leave Joey alone when his row count is not divisible by five.

    Arguments:
        wide_board: An empty 11x11 board.
        place: Helper that builds and places a piece.
    """
    joey = Coordinate(4, 4)
    board = place(wide_board, joey, PieceKind.JOEY, Color.WHITE)

    result, removed = apply_joey_explosions(board)

    assert result.piece_at(joey) is not None
    assert removed == []


def test_a_beekeeper_paralyses_adjacent_enemies_only(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Hold opposing neighbours of a BeeKeeper, leaving friendly ones free.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.BEEKEEPER, Color.WHITE)
    board = place(board, Coordinate(2, 3), PieceKind.PAWN, Color.BLACK)
    board = place(board, Coordinate(2, 1), PieceKind.PAWN, Color.WHITE)
    board = place(board, Coordinate(0, 0), PieceKind.PAWN, Color.BLACK)

    assert is_paralysed(board, Coordinate(2, 3)) is True
    assert is_paralysed(board, Coordinate(2, 1)) is False
    assert is_paralysed(board, Coordinate(0, 0)) is False


@pytest.mark.parametrize(
    "kind", [PieceKind.GOLF_CART, PieceKind.TIME_MACHINE], ids=["golf-cart", "time-machine"]
)
def test_some_pieces_cannot_be_paralysed(
    empty_board: Board, place: Callable[..., Board], kind: PieceKind
) -> None:
    """
    Exempt the Golf Cart and Time Machine from the swarm.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        kind: The immune kind under test.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.BEEKEEPER, Color.WHITE)
    board = place(board, Coordinate(2, 3), kind, Color.BLACK)

    assert is_paralysed(board, Coordinate(2, 3)) is False


def test_the_starting_position_is_active() -> None:
    """
    Report an active game while both Kings stand.
    """
    board = Variant().build_board()

    assert surviving_royals(board) == frozenset({Color.WHITE, Color.BLACK})
    assert evaluate_status(board) is GameStatus.ACTIVE


@pytest.mark.parametrize(
    "lost,expected",
    [
        (Color.BLACK, GameStatus.WHITE_WINS),
        (Color.WHITE, GameStatus.BLACK_WINS),
    ],
    ids=["white-wins", "black-wins"],
)
def test_losing_a_king_loses_the_game(
    empty_board: Board, place: Callable[..., Board], lost: Color, expected: GameStatus
) -> None:
    """
    End the game when one side has no royal piece left.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
        lost: The colour whose King is gone.
        expected: The status that should follow.
    """
    board = place(empty_board, Coordinate(0, 0), PieceKind.KING, lost.opponent)

    assert evaluate_status(board) is expected


def test_a_jet_pack_king_still_counts_as_a_king(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Keep a side alive on a Jet Pack King alone, since King includes it.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(0, 0), PieceKind.JET_PACK_KING, Color.WHITE)
    board = place(board, Coordinate(4, 4), PieceKind.KING, Color.BLACK)

    assert evaluate_status(board) is GameStatus.ACTIVE


def test_losing_both_kings_together_is_a_draw(empty_board: Board) -> None:
    """
    Call it a draw when neither side has a King, as the rules require for a
    simultaneous capture during after-effects.

    Arguments:
        empty_board: An unobstructed 5x5 board.
    """
    assert evaluate_status(empty_board) is GameStatus.DRAW


def test_the_pipeline_runs_every_phase_in_order(
    place: Callable[..., Board],
) -> None:
    """
    Run all five phases on one board and confirm the ordering matters.

    A pawn is poisoned away before it can promote, proving phase one precedes
    phase two rather than the two being independent.

    Arguments:
        place: Helper that builds and places a piece.
    """
    board = Variant().build_board()
    promoting = Coordinate(10, 4)
    board = board.without_piece(promoting)
    board = place(board, promoting, PieceKind.PAWN, Color.WHITE)
    board = board.without_piece(Coordinate(10, 3))
    board = place(board, Coordinate(10, 3), PieceKind.SERPENT, Color.BLACK)

    report = run_after_effects(board, WILDEBEEST_TRANSPORTER_LINKS)

    assert report.board.piece_at(promoting) is None
    assert PieceKind.TIME_MACHINE not in {kind for _, kind in report.promoted}


def test_the_pipeline_leaves_the_source_board_untouched() -> None:
    """
    Keep the pipeline pure, like every other transition in the domain.
    """
    board = Variant().build_board()
    cells_before = board.cells
    rendered_before = str(board)

    run_after_effects(board, WILDEBEEST_TRANSPORTER_LINKS)

    assert board.cells is cells_before
    assert str(board) == rendered_before


def test_the_starting_position_survives_the_pipeline_unchanged() -> None:
    """
    Change nothing on the opening board: no poisoner is adjacent to an enemy,
    no pawn has crossed, no cart is charged, no pad is occupied, and no Joey
    sits in a row of five.
    """
    board = Variant().build_board()

    report = run_after_effects(board, WILDEBEEST_TRANSPORTER_LINKS)

    assert str(report.board) == str(board)
    assert report.removed == ()
    assert report.promoted == ()


def test_a_grand_empress_triggers_the_old_woman_exception_too(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Reverse a Grand Empress's poisoning exactly as a Serpent's is reversed.

    The rules name only the Serpent, but the Grand Empress poisons as well and
    is herself created by this exception, so it applies to any poisoner.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    empress = Coordinate(2, 2)
    victim = Coordinate(2, 3)
    old_woman = Coordinate(2, 4)

    board = place(empty_board, empress, PieceKind.GRAND_EMPRESS, Color.WHITE)
    board = place(board, victim, PieceKind.PAWN, Color.BLACK)
    board = place(board, old_woman, PieceKind.OLD_WOMAN, Color.BLACK)

    result, removed, promoted = apply_poisoning(board)

    assert result.piece_at(victim) is not None
    assert result.piece_at(empress) is None
    assert result.require_piece_at(old_woman).kind is PieceKind.GRAND_EMPRESS
    assert [kind for _, kind in removed] == [PieceKind.GRAND_EMPRESS]
    assert [kind for _, kind in promoted] == [PieceKind.GRAND_EMPRESS]


def test_the_exception_can_produce_a_second_grand_empress(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Allow more than one Grand Empress on the board at a time.

    One side's Grand Empress is destroyed and the other side gains one, so the
    count is not capped at one per game or one per side.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.GRAND_EMPRESS, Color.WHITE)
    board = place(board, Coordinate(2, 3), PieceKind.PAWN, Color.BLACK)
    board = place(board, Coordinate(2, 4), PieceKind.OLD_WOMAN, Color.BLACK)
    board = place(board, Coordinate(4, 4), PieceKind.GRAND_EMPRESS, Color.BLACK)

    result, _, _ = apply_poisoning(board)

    empresses = [
        square for square, piece in result.pieces() if piece.kind is PieceKind.GRAND_EMPRESS
    ]
    assert sorted((square.row, square.column) for square in empresses) == [(2, 4), (4, 4)]


def test_a_newly_promoted_grand_empress_does_not_poison_in_the_same_phase(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Resolve the whole phase from the board as it stood when the phase began.

    An Old Woman promoted by the exception does not immediately poison her own
    neighbours; she will on the next turn. This matches the Joey rule, where
    every explosion is judged before any piece is removed.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    bystander = Coordinate(3, 4)

    board = place(empty_board, Coordinate(2, 2), PieceKind.SERPENT, Color.WHITE)
    board = place(board, Coordinate(2, 3), PieceKind.PAWN, Color.BLACK)
    board = place(board, Coordinate(2, 4), PieceKind.OLD_WOMAN, Color.BLACK)
    board = place(board, bystander, PieceKind.ROOK, Color.WHITE)

    result, _, _ = apply_poisoning(board)

    assert result.require_piece_at(Coordinate(2, 4)).kind is PieceKind.GRAND_EMPRESS
    assert result.piece_at(bystander) is not None


def test_the_report_names_the_phase_behind_each_removal(
    empty_board: Board, place: Callable[..., Board]
) -> None:
    """
    Tag a poisoned piece with the poison phase, for the move history.

    Arguments:
        empty_board: An unobstructed 5x5 board.
        place: Helper that builds and places a piece.
    """
    board = place(empty_board, Coordinate(2, 2), PieceKind.SERPENT, Color.WHITE)
    board = place(board, Coordinate(2, 3), PieceKind.PAWN, Color.BLACK)

    report = run_after_effects(board, {})

    victim = next(piece_id for piece_id, _ in report.removed)
    assert report.causes == ((victim, RemovalCause.POISON),)


def test_the_report_records_each_transporter_journey() -> None:
    """
    List the piece a pad carried and both pads, before the board forgets them.
    """
    board = (
        Variant()
        .build_board()
        .with_piece(Coordinate(3, 1), create_piece(900, PieceKind.ROOK, Color.WHITE))
    )

    report = run_after_effects(board, WILDEBEEST_TRANSPORTER_LINKS)

    assert report.transported == (
        Transport(
            piece_id=900,
            kind=PieceKind.ROOK,
            origin=Coordinate(3, 1),
            destination=Coordinate(7, 9),
        ),
    )
