# Wildebeest Chess

Wildebeest Chess is an 11×11 chess variant with custom pieces and special squares. The
project's goal is a website where you can play a game against a computer opponent.

The rules follow the course document *Two-Player Wildebeest (2PW), version 2.2*. Pieces
that are created during play, such as the Jet Pack King and the Time Machine, do not appear
in the starting position; see the rules for how they arise.

## Project layout

```
backend/     Python rules engine, computer opponent and HTTP API
  domain/    The rules of the game. Imports only the Python standard library.
  ai/        The computer opponent: piece values and Minimax search.
  api/       HTTP routes and error mapping (FastAPI).
  tests/     Automated tests (pytest).
frontend/    React user interface (Create React App).
```

The domain layer knows nothing about the web, so every rule can be tested without a server.
A continuous-integration check enforces this: a domain file that imports FastAPI or Pydantic
fails the build.

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

- `GET /api/v1/healthz`: reports that the server is running.
- `GET /api/v1/variants/wildebeest`: board size, every piece with its movement description,
  and the special squares.
- `http://localhost:8000/docs`: interactive API documentation.

The server keeps all game state in memory. Restarting it ends every game in progress, and it
must run as a **single worker**: `--workers N` with more than one process would split a game
across processes that cannot see each other.

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

## Using the computer opponent from Python

The opponent is available as a Python class. It is not yet reachable through the HTTP API.

```python
from backend.ai.minimax import MinimaxPlayer
from backend.domain.game import Game
from backend.domain.variant import Variant

game = Game.start("demo", Variant())
move = MinimaxPlayer().choose_move(game)   # looks two turns ahead by default
game = game.apply_move(move)
```

`MinimaxPlayer(depth=3)` searches deeper and is stronger but slower; depth 3 takes roughly a
second per move on a typical middlegame position.

## Current status

| Part | Status |
|---|---|
| Rules: board, all fifteen pieces, special squares, after-effects, win detection | Complete and tested |
| Computer opponent (Minimax with alpha-beta pruning) | Complete and tested, from Python only |
| HTTP routes for the health check and the variant description | Complete |
| HTTP routes for creating and playing games | Not built yet |
| Frontend | Work in progress |

## Contributing

Before committing, run the four checks above. Changes to the rules belong in `backend/domain/`
and need a test. Code follows the conventions in `CLAUDE.md`, including its requirement that
every function has a docstring and that SonarCloud issues are addressed.
