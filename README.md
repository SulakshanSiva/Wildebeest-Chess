# Wildebeest Chess

Wildebeest Chess is a personal project: an 11×11 chess variant with custom pieces and special
squares. The goal is a website where you can play a game against a computer opponent.

Pieces that are created during play, such as the Jet Pack King and the Time Machine, do not
appear in the starting position. They arise from the rules described in `backend/domain/`.

## Project layout

```
backend/     Python rules engine, computer opponent and HTTP API
  domain/    The rules of the game. Imports only the Python standard library.
  ai/        The computer opponent: piece values and Minimax search.
  application/  Running games: starting them, storing them in memory, playing turns.
  api/       HTTP routes and error mapping (FastAPI).
  tests/     Automated tests (pytest).
frontend/    React user interface (Create React App).
```

Only the `api/` layer knows about the web, so every rule and the whole game service can be
tested without a server. A continuous-integration check enforces this: a domain or
application file that imports FastAPI or Pydantic fails the build.

## Requirements

- **Python 3.11** or newer
- **uv**, the Python package manager, used to install locked dependencies
- **Node.js** and npm, for the frontend

## Running the backend

From the repository root:

```bash
uv sync --extra dev
uv run uvicorn backend.main:app --reload
```

The API then runs at `http://localhost:8000`. Useful endpoints:

- `POST /api/v1/games`: start a game against the computer.
- `POST /api/v1/games/{game_id}/moves`: make your move; the computer replies in the same response.
- `GET /api/v1/games/{game_id}`: fetch a game as it stands, for example after a page reload.
- `POST /api/v1/games/{game_id}/resign`: concede the game to the computer.
- `GET /api/v1/variants/wildebeest`: board size, every piece with its movement description,
  and the special squares.
- `GET /api/v1/healthz`: reports that the server is running.
- `http://localhost:8000/docs`: interactive API documentation, where every endpoint can be tried.

The server keeps all game state in memory. Restarting it ends every game in progress, and it
must run as a **single worker**: `--workers N` with more than one process would split a game
across processes that cannot see each other. A game nobody touches for an hour is dropped.

These environment variables adjust the server; each is optional:

| Variable | Default | Meaning |
|---|---|---|
| `WILDEBEEST_AI_DEPTH` | `2` | How many turns ahead the computer looks |
| `WILDEBEEST_GAME_TTL_SECONDS` | `3600` | How long an untouched game is kept |
| `WILDEBEEST_MAX_GAMES` | `1000` | The most games held in memory at once |
| `WILDEBEEST_CORS_ORIGINS` | `http://localhost:3000` | Browser origins allowed to call the API, comma-separated |

## Running the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run start
```

The interface opens at `http://localhost:3000`. It is not the current focus of the project,
so it is still a work in progress.

## Running the tests and checks

These are the same four checks that run in continuous integration, in this order:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

`pytest` reports a test count and a coverage file, `coverage.xml`, that SonarCloud reads.

Continuous integration then runs the frontend tests, which write `frontend/coverage/lcov.info`
for SonarCloud too:

```bash
cd frontend
CI=true npm test -- --watchAll=false --coverage
```

## Playing a game through the API

Start a game. `human_color` is `white` or `black`; as Black, the computer's first move is
already played in the response.

```bash
curl -X POST localhost:8000/api/v1/games -H 'Content-Type: application/json' -d '{"human_color": "white"}'
```

The response holds the `game_id`, the board, your `legal_moves` and the game's `version`.
Make a move by sending one of those legal moves' squares, with the version you were shown:

```bash
curl -X POST localhost:8000/api/v1/games/GAME_ID/moves -H 'Content-Type: application/json' \
  -d '{"origin": {"row": 0, "column": 1}, "destination": {"row": 2, "column": 2}, "expected_version": 0}'
```

The response shows the board after your move and the computer's reply, both listed in `turns`,
and a new `version` to send with your next move. A move sent with an out-of-date version is
refused with `409 Conflict`, so a double-click or a second browser tab can never apply a move to
a position you did not see.

Squares are zero-based: row 0 is White's back row and column 0 is the left edge.

To concede, resign. No body is needed; the game ends as a win for the computer.

```bash
curl -X POST localhost:8000/api/v1/games/GAME_ID/resign
```

## Current status

| Part | Status |
|---|---|
| Rules: board, all fifteen pieces, special squares, after-effects, win detection | Complete and tested |
| Computer opponent (Minimax with alpha-beta pruning) | Complete and tested |
| Game service and in-memory game store | Complete and tested |
| HTTP API for starting, playing, reloading and resigning games | Complete and tested |
| Frontend | Work in progress |

## Contributing

Before committing, run the four checks above. Changes to the rules belong in `backend/domain/`
and need a test. Code follows the conventions in `CLAUDE.md`, including its requirement that
every function has a docstring and that SonarCloud issues are addressed.
