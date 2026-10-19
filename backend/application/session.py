from __future__ import annotations

from dataclasses import dataclass, replace

from ..domain.enums import Color
from ..domain.game import Game


@dataclass(frozen=True, slots=True)
class GameSession:
    """
    A game together with who is playing which side.

    The Game knows the rules but not that one side is a person and the other the
    computer, which is a fact about this application rather than about chess.

    Attributes:
        game: The game being played.
        human_color: The colour the person plays. The AI plays the other.
    """

    game: Game
    human_color: Color

    @property
    def game_id(self) -> str:
        """
        Give the identifier of the game.

        Returns:
            The game's id.
        """
        return self.game.game_id

    @property
    def ai_color(self) -> Color:
        """
        Give the colour the computer plays.

        Returns:
            The opposite of the human's colour.
        """
        return self.human_color.opponent

    def with_game(self, game: Game) -> GameSession:
        """
        Give a copy of this session holding a newer version of the game.

        Arguments:
            game: The replacement game.

        Returns:
            A new session with the same players.
        """
        return replace(self, game=game)
