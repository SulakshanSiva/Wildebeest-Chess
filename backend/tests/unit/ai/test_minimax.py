from __future__ import annotations

import random

import pytest

from backend.ai.minimax import DEFAULT_DEPTH, REPETITION_PENALTY, MinimaxPlayer
from backend.ai.piece_values import value_of
from backend.domain.board import Board, BoardDimensions
from backend.domain.coordinates import Coordinate
from backend.domain.enums import Color, GameStatus, MoveAction, PieceKind
from backend.domain.errors import GameOverError
from backend.domain.game import Game
from backend.domain.pieces.registry import create_piece
from backend.domain.position import Position
from backend.domain.variant import Variant

WHITE_KING = (Coordinate(0, 0), PieceKind.KING, Color.WHITE)
BLACK_KING = (Coordinate(10, 10), PieceKind.KING, Color.BLACK)
PLAYOUT_SEEDS = range(5)
PLAYOUT_TURNS = 30


def _game(pieces: list[tuple[Coordinate, PieceKind, Color]], side: Color = Color.WHITE) -> Game:
    """
    Build a game holding exactly the given pieces.

    Arguments:
        pieces: Every piece on the board, as square, kind and colour.
        side: The colour to move.

    Returns:
        A game on an empty 11x11 board with those pieces placed.
    """
    board = Board.empty(BoardDimensions(11, 11))
    for index, (square, kind, colour) in enumerate(pieces, start=1):
        board = board.with_piece(square, create_piece(index, kind, colour))
    return Game(game_id="ai", variant=Variant(), position=Position(board=board, side_to_move=side))


def test_the_default_depth_sees_the_opponents_reply() -> None:
    """
    Look at least two turns ahead by default: the AI's move and the answer to it.
    """
    assert DEFAULT_DEPTH >= 2
    assert MinimaxPlayer().depth == DEFAULT_DEPTH


def test_a_depth_below_one_is_refused() -> None:
    """
    Reject a depth that would search nothing.
    """
    with pytest.raises(ValueError, match="at least 1"):
        MinimaxPlayer(depth=0)


def test_it_takes_a_free_piece() -> None:
    """
    Capture an undefended enemy piece when one is available.
    """
    game = _game(
        [
            WHITE_KING,
            BLACK_KING,
            (Coordinate(5, 0), PieceKind.ROOK, Color.WHITE),
            (Coordinate(5, 8), PieceKind.ROOK, Color.BLACK),
        ]
    )

    move = MinimaxPlayer(depth=1).choose_move(game)

    assert move.action is MoveAction.CAPTURE
    assert move.destination == Coordinate(5, 8)


def test_it_takes_the_king_over_any_other_capture() -> None:
    """
    Win the game outright rather than grab the most valuable ordinary piece.
    """
    game = _game(
        [
            WHITE_KING,
            (Coordinate(10, 5), PieceKind.KING, Color.BLACK),
            (Coordinate(10, 0), PieceKind.ROOK, Color.WHITE),
            (Coordinate(4, 0), PieceKind.GRAND_EMPRESS, Color.BLACK),
        ]
    )

    move = MinimaxPlayer(depth=1).choose_move(game)
    after = game.apply_move(move)

    assert move.destination == Coordinate(10, 5)
    assert after.status is GameStatus.WHITE_WINS


def test_looking_ahead_avoids_a_defended_pawn() -> None:
    """
    Refuse a pawn that is guarded, which only a two-turn search can see.

    At depth one the pawn looks like a free point; at depth two the AI sees the
    rook it would lose to the recapture, and declines.
    """
    pieces = [
        WHITE_KING,
        BLACK_KING,
        (Coordinate(5, 0), PieceKind.ROOK, Color.WHITE),
        (Coordinate(5, 5), PieceKind.PAWN, Color.BLACK),
        (Coordinate(9, 5), PieceKind.ROOK, Color.BLACK),
    ]
    guarded_pawn = Coordinate(5, 5)

    shallow = MinimaxPlayer(depth=1).choose_move(_game(pieces))
    deep = MinimaxPlayer(depth=2).choose_move(_game(pieces))

    assert shallow.destination == guarded_pawn
    assert deep.destination != guarded_pawn


@pytest.mark.parametrize("side", [Color.WHITE, Color.BLACK], ids=["white", "black"])
def test_it_never_sets_off_its_own_joey_in_the_opening(side: Color) -> None:
    """
    Avoid the opening trap where emptying the home row makes Joey explode.

    Most opening moves take a piece off row 1 or row 9, which leaves ten pieces
    there and detonates that side's own Joey beside its King. The search plays
    whole turns, after-effects included, so it sees the explosion coming.

    Arguments:
        side: The colour the AI plays.
    """
    game = Game.start("opening", Variant())
    if side is Color.BLACK:
        game = game.apply_move(game.find_move(Coordinate(0, 1), Coordinate(2, 2)))

    move = MinimaxPlayer(depth=1).choose_move(game)

    assert game.apply_move(move).status is GameStatus.ACTIVE


def test_the_same_position_always_gives_the_same_move() -> None:
    """
    Choose deterministically, so a game and a test can be reproduced.
    """
    game = Game.start("repeat", Variant())

    first = MinimaxPlayer().choose_move(game)
    second = MinimaxPlayer().choose_move(game)

    assert first == second


def test_choosing_a_move_leaves_the_game_untouched() -> None:
    """
    Search hypothetical positions without changing the real game.
    """
    game = Game.start("pure", Variant())
    before = str(game.position.board)

    MinimaxPlayer().choose_move(game)

    assert str(game.position.board) == before
    assert game.version == 0
    assert game.history == ()


def test_a_finished_game_cannot_be_moved_in() -> None:
    """
    Refuse to search a game that is already decided.
    """
    over = Game.start("over", Variant()).resign(Color.WHITE)

    with pytest.raises(GameOverError):
        MinimaxPlayer().choose_move(over)


@pytest.mark.parametrize("seed", PLAYOUT_SEEDS)
def test_every_chosen_move_is_legal(seed: int) -> None:
    """
    Play the AI against random moves and check each of its choices is legal.

    Arguments:
        seed: Seed for the random opponent, for reproducibility.
    """
    rng = random.Random(seed)
    ai = MinimaxPlayer(depth=1)
    game = Game.start(f"vs-random-{seed}", Variant())

    for _ in range(PLAYOUT_TURNS):
        if game.status.is_over:
            break
        if game.side_to_move is Color.WHITE:
            move = ai.choose_move(game)
            assert move in game.legal_moves()
        else:
            move = rng.choice(game.legal_moves())
        game = game.apply_move(move)


def test_it_does_not_shuffle_back_into_a_position_it_has_played() -> None:
    """
    Stop the Joey shuffle: with material level, step to new positions instead.

    Before the repetition penalty and the pressure term, every quiet move scored
    the same, so the AI took the first one every turn and moved Prince Joey
    F10 to F9 and back for as long as the opponent kept shuffling too.
    """
    game = Game.start("shuffle", Variant())
    ai = MinimaxPlayer()
    knight_out = (Coordinate(0, 9), Coordinate(2, 8))

    for turn in range(6):
        origin, destination = knight_out if turn % 2 == 0 else knight_out[::-1]
        game = game.apply_move(game.find_move(origin, destination))
        played = game.seen_positions

        game = game.apply_move(ai.choose_move(game))

        assert game.position.repetition_key not in played


def test_avoiding_a_repeat_is_never_worth_a_pawn() -> None:
    """
    Keep the penalty below the smallest piece, so the AI never gives away
    material just to avoid repeating a position.
    """
    assert 0 < REPETITION_PENALTY < value_of(PieceKind.PAWN)
