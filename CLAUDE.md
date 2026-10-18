# Wildebeest-Chess

# About

Wildebeest Chess is a chess game with custom pieces. The goal of this project is to create a website where a user can play against
an AI opponent and play a game of chess.

## Frontend

All frontend code exists in the /frontend folder.

Currently, we are not focused on developing a UI.

To run the frontend, use the following command in the frontend directory.

```
npm run start
```

## Backend

To run the backend, use the following command from the repository root.

```
uvicorn backend.main:app --reload
```

`backend/main.py` holds the application factory. `backend/server.py` remains only as a
compatibility shim that re-exports the same app.

## Database

This project has no database by design, and will not be given one. Game states are
never persisted and there is no player data or accounts.

Games live in process memory only, for the lifetime of the server process. This means:

- Run a single worker. `uvicorn --workers N` breaks games, because the request that
  creates a game and the request that moves in it can land on different processes.
- Abandoned games must be evicted (TTL or an LRU cap). Unbounded memory growth is the
  main operational risk here, in place of the usual persistence concerns.
- Restarting the server ends every game in progress. That is acceptable.

Do not add SQLAlchemy, Alembic, a Redis-backed store, auth, or sessions.

## Quality Gates

Four checks must pass before anything merges. CI runs them in this order, cheapest
first, in `.github/workflows/backend.yml`. Run them locally with:

```
python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy && python3 -m pytest
```

Install the tooling with `python3 -m pip install -e ".[dev]"`. Configuration lives in
`pyproject.toml`, not in separate config files.

The lint step enforces the architecture, not just style: `backend/domain/` is banned
from importing `fastapi`, `pydantic`, `sqlalchemy`, or `redis`, so a dependency-direction
violation fails CI instead of relying on a reviewer to notice it.

## Programming Practices

### Comments

- All functions should have a function header comment with a description, arguments and return values. This comment starts on a new line after the """
- Files should never have a file comment at the top of the file
- Comments should be used to explain code within 1 - 2 lines

### Sonar

- All sonar issues should be addressed
