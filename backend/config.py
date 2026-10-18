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
    """

    api_prefix: str = "/api/v1"
    cors_origins: tuple[str, ...] = field(default_factory=lambda: DEFAULT_CORS_ORIGINS)

    @classmethod
    def from_environment(cls) -> Settings:
        """
        Build settings from environment variables, falling back to defaults.

        Returns:
            A settings object. Unset variables keep their default.
        """
        origins = os.environ.get("WILDEBEEST_CORS_ORIGINS")
        return cls(
            api_prefix=os.environ.get("WILDEBEEST_API_PREFIX", "/api/v1"),
            cors_origins=tuple(origins.split(",")) if origins else DEFAULT_CORS_ORIGINS,
        )
