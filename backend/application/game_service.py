from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass

from ..ai.minimax import MinimaxPlayer
from ..domain.coordinates import Coordinate
from ..domain.enums import Color
from ..domain.game import Game
from ..domain.move import MoveRecord
from ..domain.variant import Variant
from .game_store import InMemoryGameStore
from .session import GameSession


@dataclass(frozen=True, slots=True)
class GameView:
    """
    What a request gets back: the game as it now stands, and the turns it caused.

    Attributes:
        session: The game and its players.
        turns: The turns this request played, oldest first: none for a lookup,
            the human's move and the AI's reply for a move.
    """

    session: GameSession
    turns: tuple[MoveRecord, ...] = ()


def _new_game_id() -> str:
    """
    Make an identifier for a new game.

    Returns:
        A random, unguessable id, so one player cannot move in another's game.
    """
    return uuid.uuid4().hex


class GameService:
    """
    The use cases of the application: start a game, look at it, make a move.

    Holds no rules of its own. It finds the game, asks the Game to apply a move,
    asks the AI for its reply, and stores the result. Every rule lives in the
    domain, so a move is judged identically however it arrives.
    """

    def __init__(
        self,
        store: InMemoryGameStore,
        ai: MinimaxPlayer,
        variant: Variant,
        new_game_id: Callable[[], str] = _new_game_id,
    ) -> None:
        """
        Build the service from its collaborators.

        Arguments:
            store: Where games are kept between requests.
            ai: The computer opponent.
            variant: The ruleset new games are played under.
            new_game_id: Source of ids for new games, replaceable in tests.
        """
        self._store = store
        self._ai = ai
        self._variant = variant
        self._new_game_id = new_game_id

    def create_game(self, human_color: Color) -> GameView:
        """
        Start a game with the person playing the colour of their choice.

        White moves first, so when the person plays Black the AI makes the
        opening move before the game is handed back.

        Arguments:
            human_color: The colour the person plays.

        Returns:
            The new game, ready for the person's move, and any AI move played.
        """
        session = GameSession(
            game=Game.start(self._new_game_id(), self._variant),
            human_color=human_color,
        )
        session, turns = self._play_ai_turn(session)
        self._store.add(session)
        return GameView(session=session, turns=turns)

    def get_game(self, game_id: str) -> GameView:
        """
        Look up a game as it stands.

        Arguments:
            game_id: The game to look up.

        Returns:
            The game, with no turns, since looking changes nothing.
        """
        return GameView(session=self._store.get(game_id))

    def submit_move(
        self,
        game_id: str,
        origin: Coordinate,
        destination: Coordinate,
        expected_version: int,
        actor: Coordinate | None = None,
    ) -> GameView:
        """
        Play the person's move, then the AI's reply, as one change to the game.

        Both moves are applied under the game's lock, so nothing can happen
        between them. If the person's move is refused, nothing is stored.

        Arguments:
            game_id: The game to move in.
            origin: Square of the piece the person moves.
            destination: Square it moves to.
            expected_version: The game version the person last saw. A different
                version means the game changed since, and the move is refused.
            actor: Square of the piece spending the turn, needed only when
                origin and destination alone could name more than one move.

        Returns:
            The game after both moves, and the turns that were played.
        """

        def play(session: GameSession) -> tuple[GameSession, GameView]:
            """
            Apply the person's move and the AI's reply to one session.

            Arguments:
                session: The game as it stands.

            Returns:
                The updated session, and the view to hand back.
            """
            game = session.game
            game.require_current(expected_version)
            move = game.find_move(origin, destination, actor)
            after_human = session.with_game(game.apply_move(move, expected_version))
            after_ai, ai_turns = self._play_ai_turn(after_human)
            turns = (after_human.game.history[-1], *ai_turns)
            return after_ai, GameView(session=after_ai, turns=turns)

        return self._store.update(game_id, play)

    def resign(self, game_id: str) -> GameView:
        """
        End a game with the person conceding to the computer.

        No version is asked for: resigning means "I give up", which is true
        whatever the board shows. A game that has already ended cannot be
        resigned, and that is still refused.

        Arguments:
            game_id: The game to resign.

        Returns:
            The finished game, won by the computer, with no turns played.
        """

        def concede(session: GameSession) -> tuple[GameSession, GameView]:
            """
            Record the person's resignation on one session.

            Arguments:
                session: The game as it stands.

            Returns:
                The finished session, and the view to hand back.
            """
            resigned = session.with_game(session.game.resign(session.human_color))
            return resigned, GameView(session=resigned)

        return self._store.update(game_id, concede)

    def _play_ai_turn(self, session: GameSession) -> tuple[GameSession, tuple[MoveRecord, ...]]:
        """
        Let the AI move, if it is the AI's turn and the game is still going.

        Arguments:
            session: The game as it stands.

        Returns:
            The session after the AI's move, and the turn it played, or the
            session unchanged and no turns if the AI had nothing to do.
        """
        game = session.game
        if game.status.is_over or game.side_to_move is not session.ai_color:
            return session, ()
        played = game.apply_move(self._ai.choose_move(game))
        return session.with_game(played), (played.history[-1],)
