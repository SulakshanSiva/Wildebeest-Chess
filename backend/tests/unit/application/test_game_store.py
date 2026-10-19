from __future__ import annotations

import threading

import pytest

from backend.application.errors import GameNotFoundError
from backend.application.game_store import InMemoryGameStore
from backend.application.session import GameSession
from backend.domain.enums import Color
from backend.domain.game import Game
from backend.domain.variant import Variant

TTL = 60.0


class FakeClock:
    """
    A clock the test moves by hand, so expiry is tested without waiting.
    """

    def __init__(self) -> None:
        """
        Start the clock at zero.
        """
        self.now = 0.0

    def __call__(self) -> float:
        """
        Give the current reading.

        Returns:
            The time the test has set.
        """
        return self.now


def _session(game_id: str) -> GameSession:
    """
    Build a fresh session for a game id.

    Arguments:
        game_id: Identifier for the game.

    Returns:
        A new game with the person playing White.
    """
    return GameSession(game=Game.start(game_id, Variant()), human_color=Color.WHITE)


@pytest.fixture
def clock() -> FakeClock:
    """
    Give a clock starting at zero.

    Returns:
        A hand-driven clock.
    """
    return FakeClock()


@pytest.fixture
def store(clock: FakeClock) -> InMemoryGameStore:
    """
    Give an empty store holding up to three games.

    Arguments:
        clock: The hand-driven clock the store reads.

    Returns:
        A store with a short, testable capacity.
    """
    return InMemoryGameStore(ttl_seconds=TTL, max_games=3, clock=clock)


def test_a_stored_game_can_be_fetched(store: InMemoryGameStore) -> None:
    """
    Return the session that was added.

    Arguments:
        store: An empty store.
    """
    session = _session("a")
    store.add(session)

    assert store.get("a") is session


def test_an_unknown_game_is_not_found(store: InMemoryGameStore) -> None:
    """
    Raise a named error for an id the store has never seen.

    Arguments:
        store: An empty store.
    """
    with pytest.raises(GameNotFoundError):
        store.get("missing")


def test_an_untouched_game_expires(store: InMemoryGameStore, clock: FakeClock) -> None:
    """
    Drop a game nobody has used for longer than the time-to-live.

    Arguments:
        store: An empty store.
        clock: The store's clock.
    """
    store.add(_session("a"))
    clock.now = TTL + 1

    with pytest.raises(GameNotFoundError):
        store.get("a")
    assert len(store) == 0


def test_using_a_game_keeps_it_alive(store: InMemoryGameStore, clock: FakeClock) -> None:
    """
    Reset the time-to-live each time a game is used.

    Arguments:
        store: An empty store.
        clock: The store's clock.
    """
    store.add(_session("a"))
    clock.now = TTL - 1
    store.get("a")
    clock.now = 2 * TTL - 2

    assert store.get("a").game_id == "a"


def test_a_full_store_drops_the_least_recently_used_game(
    store: InMemoryGameStore, clock: FakeClock
) -> None:
    """
    Make room for a new game by evicting the one used longest ago.

    Arguments:
        store: An empty store holding up to three games.
        clock: The store's clock.
    """
    for tick, game_id in enumerate(["a", "b", "c"]):
        clock.now = float(tick)
        store.add(_session(game_id))
    clock.now = 3.0
    store.get("a")

    clock.now = 4.0
    store.add(_session("d"))

    assert len(store) == 3
    with pytest.raises(GameNotFoundError):
        store.get("b")
    assert store.get("a").game_id == "a"


def test_an_update_stores_the_new_session_and_returns_its_result(
    store: InMemoryGameStore,
) -> None:
    """
    Keep what the change returned, and hand back its result.

    Arguments:
        store: An empty store.
    """
    store.add(_session("a"))
    replacement = _session("a")

    result = store.update("a", lambda _current: (replacement, "done"))

    assert result == "done"
    assert store.get("a") is replacement


def test_a_failed_update_stores_nothing(store: InMemoryGameStore) -> None:
    """
    Leave the game as it was when the change raises.

    Arguments:
        store: An empty store.
    """
    original = _session("a")
    store.add(original)

    def failing(_current: GameSession) -> tuple[GameSession, None]:
        """
        Fail partway through a change.

        Arguments:
            _current: The session, unused.

        Returns:
            Never returns.
        """
        raise RuntimeError("change failed")

    with pytest.raises(RuntimeError):
        store.update("a", failing)
    assert store.get("a") is original


def test_updates_to_one_game_run_one_at_a_time(store: InMemoryGameStore) -> None:
    """
    Serialise changes to a game, so two never see the same starting state.

    Each change reads a counter, pauses, then writes it back plus one. Without
    the per-game lock both threads would read the same value and one increment
    would be lost.

    Arguments:
        store: An empty store.
    """
    store.add(_session("a"))
    seen: list[int] = []
    gate = threading.Barrier(2)

    def bump(current: GameSession) -> tuple[GameSession, None]:
        """
        Record the version seen, then advance the game's version by one.

        Arguments:
            current: The session as the change finds it.

        Returns:
            The session with its version advanced by one.
        """
        seen.append(current.game.version)
        game = current.game
        advanced = type(game)(
            game_id=game.game_id,
            variant=game.variant,
            position=game.position,
            version=game.version + 1,
        )
        return current.with_game(advanced), None

    def worker() -> None:
        """
        Wait for the other thread, then change the game.
        """
        gate.wait()
        store.update("a", bump)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(seen) == [0, 1]
    assert store.get("a").game.version == 2


@pytest.mark.parametrize("ttl,max_games", [(0, 3), (60, 0)], ids=["no-lifetime", "no-capacity"])
def test_a_store_that_could_hold_nothing_is_refused(ttl: float, max_games: int) -> None:
    """
    Reject limits that would make every game vanish at once.

    Arguments:
        ttl: The time-to-live to try.
        max_games: The capacity to try.
    """
    with pytest.raises(ValueError):
        InMemoryGameStore(ttl_seconds=ttl, max_games=max_games)
