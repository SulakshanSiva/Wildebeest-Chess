from __future__ import annotations


class ApplicationError(Exception):
    """
    Base class for expected failures in the application layer.

    Kept apart from DomainError because these are about the service around the
    game, such as which games exist, rather than about the rules of the game.
    """


class GameNotFoundError(ApplicationError):
    """
    Raised when a game id names no game the server is holding.

    An expired game raises this too: once evicted, a game is gone for good.
    """

    def __init__(self, game_id: str) -> None:
        """
        Build the error from the id that matched nothing.

        Arguments:
            game_id: The identifier that was looked up.
        """
        super().__init__(f"No game with id {game_id!r}.")
        self.game_id = game_id
