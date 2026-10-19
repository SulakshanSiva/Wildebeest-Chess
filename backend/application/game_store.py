from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from .errors import GameNotFoundError
from .session import GameSession

T = TypeVar("T")


@dataclass(slots=True)
class _Entry:
    """
    One stored game, with its lock and when it was last used.

    Attributes:
        session: The game and its players.
        lock: Held while a request changes this game, so two moves cannot
            interleave. Each game has its own, so games never wait on each other.
        last_used: Clock reading of the last time any request touched the game.
    """

    session: GameSession
    lock: threading.Lock
    last_used: float


class InMemoryGameStore:
    """
    Holds every game in progress, in this process's memory.

    There is no database by design, so a restart ends every game. Two limits keep
    memory bounded: a game nobody has touched for the time-to-live is dropped,
    and once the store is full the least recently used game makes room for a new
    one. Because games live in one process's memory, the server must run as a
    single worker.
    """

    def __init__(
        self,
        ttl_seconds: float,
        max_games: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """
        Build an empty store.

        Arguments:
            ttl_seconds: How long an untouched game is kept.
            max_games: The most games held at once.
            clock: Source of the current time, replaceable in tests.
        """
        if ttl_seconds <= 0 or max_games < 1:
            raise ValueError("ttl_seconds must be positive and max_games at least 1")
        self._ttl = ttl_seconds
        self._max_games = max_games
        self._clock = clock
        self._entries: dict[str, _Entry] = {}
        # Guards the dictionary itself. Held only briefly, never during a move.
        self._lock = threading.Lock()

    def __len__(self) -> int:
        """
        Count the games currently held.

        Returns:
            The number of stored games.
        """
        with self._lock:
            return len(self._entries)

    def add(self, session: GameSession) -> None:
        """
        Store a new game, making room first if the store is full.

        Arguments:
            session: The new game and its players.
        """
        with self._lock:
            now = self._clock()
            self._evict_expired(now)
            while len(self._entries) >= self._max_games:
                oldest = min(self._entries, key=lambda key: self._entries[key].last_used)
                del self._entries[oldest]
            self._entries[session.game_id] = _Entry(session, threading.Lock(), now)

    def get(self, game_id: str) -> GameSession:
        """
        Fetch a game, counting the lookup as use.

        Arguments:
            game_id: The game to fetch.

        Returns:
            The stored session.
        """
        with self._lock:
            entry = self._live_entry(game_id)
            entry.last_used = self._clock()
            return entry.session

    def update(self, game_id: str, change: Callable[[GameSession], tuple[GameSession, T]]) -> T:
        """
        Change one game while no other request can change it.

        The change runs under that game's own lock, so two moves submitted at
        once are applied one after the other rather than both against the same
        position. The store's main lock is released first, so a slow change to
        one game, such as an AI search, never delays any other game.

        Arguments:
            game_id: The game to change.
            change: Takes the current session and returns the new session plus
                any result to hand back. If it raises, nothing is stored.

        Returns:
            Whatever the change returned alongside the new session.
        """
        with self._lock:
            entry = self._live_entry(game_id)

        with entry.lock:
            updated, result = change(entry.session)
            with self._lock:
                # The game may have been evicted while the change ran.
                if self._entries.get(game_id) is not entry:
                    raise GameNotFoundError(game_id)
                entry.session = updated
                entry.last_used = self._clock()
        return result

    def _live_entry(self, game_id: str) -> _Entry:
        """
        Find an entry that has not expired, dropping it if it has.

        Must be called with the store's main lock held.

        Arguments:
            game_id: The game to find.

        Returns:
            The entry.
        """
        entry = self._entries.get(game_id)
        if entry is None:
            raise GameNotFoundError(game_id)
        if self._clock() - entry.last_used > self._ttl:
            del self._entries[game_id]
            raise GameNotFoundError(game_id)
        return entry

    def _evict_expired(self, now: float) -> None:
        """
        Drop every game untouched for longer than the time-to-live.

        Must be called with the store's main lock held.

        Arguments:
            now: The current clock reading.
        """
        expired = [key for key, entry in self._entries.items() if now - entry.last_used > self._ttl]
        for key in expired:
            del self._entries[key]
