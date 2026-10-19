from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_CORS_ORIGINS = ("http://localhost:3000",)


@dataclass(frozen=True, slots=True)
class Settings:
    """
    Environment-backed application settings.

    Read once at startup and injected into the app factory, so nothing reads
    os.environ at import time and tests can pass settings explicitly.

    Attributes:
        api_prefix: Version prefix every route hangs off.
        cors_origins: Browser origins allowed to call the API.
        game_ttl_seconds: How long a game nobody touches is kept before eviction.
        max_games: The most games held in memory at once.
        ai_depth: How many turns ahead the computer opponent looks.
    """

    api_prefix: str = "/api/v1"
    cors_origins: tuple[str, ...] = field(default_factory=lambda: DEFAULT_CORS_ORIGINS)
    game_ttl_seconds: int = 3600
    max_games: int = 1000
    ai_depth: int = 2

    @classmethod
    def from_environment(cls) -> Settings:
        """
        Build settings from environment variables, falling back to defaults.

        Returns:
            A settings object. Unset variables keep their default.
        """
        origins = os.environ.get("WILDEBEEST_CORS_ORIGINS")
        defaults = cls()
        return cls(
            api_prefix=os.environ.get("WILDEBEEST_API_PREFIX", defaults.api_prefix),
            cors_origins=tuple(origins.split(",")) if origins else DEFAULT_CORS_ORIGINS,
            game_ttl_seconds=_int_env("WILDEBEEST_GAME_TTL_SECONDS", defaults.game_ttl_seconds),
            max_games=_int_env("WILDEBEEST_MAX_GAMES", defaults.max_games),
            ai_depth=_int_env("WILDEBEEST_AI_DEPTH", defaults.ai_depth),
        )


def _int_env(name: str, default: int) -> int:
    """
    Read a whole-number setting from the environment.

    Arguments:
        name: The environment variable to read.
        default: The value to use when it is unset.

    Returns:
        The variable as an integer, or the default.
    """
    raw = os.environ.get(name)
    return default if raw is None else int(raw)
