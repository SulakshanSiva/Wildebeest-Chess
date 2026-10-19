from __future__ import annotations

from dataclasses import dataclass, replace

from .coordinates import Coordinate
from .enums import Color, EndReason, GameStatus
from .errors import AmbiguousMoveError, GameOverError, IllegalMoveError, StaleVersionError
from .move import Move, MoveRecord
from .position import Position
from .rules.move_generator import legal_moves
from .rules.turn import resolve_turn
from .variant import Variant


@dataclass(frozen=True, slots=True)
class Game:
    """
    One game from its first position to its end, and the only way to change it.

    The aggregate root. Callers never reach in to edit the board: they ask for a
    move, and the game validates it, applies it, runs the after-effects, judges
    the result and returns a new game. Because it is immutable, a game that is
    being read by one request cannot be altered under it by another.

    Attributes:
        game_id: Stable identifier.
        variant: The ruleset, which supplies the transporter links.
        position: The current board and side to move.
        history: Every applied move, oldest first, enough to replay the game.
        status: Whether the game is active or who won.
        end_reason: Why it ended, or None while it is active.
        version: Incremented on every change, for optimistic concurrency.
    """

    game_id: str
    variant: Variant
    position: Position
    history: tuple[MoveRecord, ...] = ()
    status: GameStatus = GameStatus.ACTIVE
    end_reason: EndReason | None = None
    version: int = 0

    @classmethod
    def start(cls, game_id: str, variant: Variant) -> Game:
        """
        Begin a new game from a variant's starting position.

        Arguments:
            game_id: Identifier to give the game.
            variant: The ruleset to play.

        Returns:
            A game at version zero with the first player to move.
        """
        return cls(game_id=game_id, variant=variant, position=variant.initial_position())

    @property
    def side_to_move(self) -> Color:
        """
        Give the colour whose turn it is.

        Returns:
            The side to move in the current position.
        """
        return self.position.side_to_move

    def legal_moves(self) -> tuple[Move, ...]:
        """
        List every move the side to move may make.

        Returns:
            The legal moves, or nothing once the game is over.
        """
        if self.status.is_over:
            return ()
        return legal_moves(self.position.board, self.side_to_move)

    def require_current(self, expected_version: int | None = None) -> None:
        """
        Confirm the game can still be changed by a caller who saw a given version.

        Checked before anything else a command does, so a caller who is out of
        date hears that first rather than an error about a move that was only
        illegal because the game had moved on.

        Arguments:
            expected_version: The version the caller last saw, or None to skip
                the version check.
        """
        if self.status.is_over:
            raise GameOverError
        if expected_version is not None and expected_version != self.version:
            raise StaleVersionError(expected_version, self.version)

    def find_move(
        self,
        origin: Coordinate,
        destination: Coordinate,
        actor: Coordinate | None = None,
    ) -> Move:
        """
        Resolve a pair of squares into the one legal move they name.

        A client names squares rather than constructing a Move. Squares nearly
        always identify a move uniquely, since a fling is a straight line past
        a Catapult that blocks every other piece's route to the same landing.
        The optional actor exists for any position where they do not.

        Arguments:
            origin: Square of the piece that moves.
            destination: Square it ends on.
            actor: Square of the piece spending the turn, to disambiguate.

        Returns:
            The single matching legal move.
        """
        matches = [
            move
            for move in self.legal_moves()
            if move.origin == origin
            and move.destination == destination
            and (actor is None or move.actor == actor)
        ]
        if not matches:
            raise IllegalMoveError(f"no legal move from {origin} to {destination}")
        if len(matches) > 1:
            raise AmbiguousMoveError(
                f"{len(matches)} legal moves from {origin} to {destination}; name the actor"
            )
        return matches[0]

    def apply_move(self, move: Move, expected_version: int | None = None) -> Game:
        """
        Play a move for the side to move and return the resulting game.

        The turn runs in a fixed order: the move, then the five after-effect
        phases, then the verdict. The verdict has to come last, because poison,
        a rampage, an explosion or a crush can take a King as surely as a
        capture can.

        Arguments:
            move: The move to play. Must be one of the legal moves.
            expected_version: The version the caller last saw, or None to skip
                the check. A mismatch means someone else moved first.

        Returns:
            A new game with the move applied and the turn handed over.
        """
        self.require_current(expected_version)
        if move not in self.legal_moves():
            raise IllegalMoveError(f"{move} is not legal for {self.side_to_move.value}")

        before = self.position.board
        mover = before.require_piece_at(move.actor)
        result = resolve_turn(self.position, move, self.variant.transporter_links)

        survivors = {piece.piece_id for _, piece in result.position.board.pieces()}
        captured = tuple(
            (piece.piece_id, piece.kind)
            for _, piece in before.pieces()
            if piece.piece_id not in survivors
        )
        record = MoveRecord(
            move=move,
            moved_piece_id=mover.piece_id,
            side=self.side_to_move,
            captured=captured,
            promoted=result.report.promoted,
            ply=len(self.history),
        )

        return replace(
            self,
            position=result.position,
            history=(*self.history, record),
            status=result.status,
            end_reason=result.end_reason,
            version=self.version + 1,
        )

    def resign(self, side: Color, expected_version: int | None = None) -> Game:
        """
        End the game with one side conceding to the other.

        Arguments:
            side: The colour that resigns.
            expected_version: The version the caller last saw, or None.

        Returns:
            A finished game won by the opponent of the resigning side.
        """
        self.require_current(expected_version)

        winner = GameStatus.WHITE_WINS if side is Color.BLACK else GameStatus.BLACK_WINS
        return replace(
            self,
            status=winner,
            end_reason=EndReason.RESIGNATION,
            version=self.version + 1,
        )
