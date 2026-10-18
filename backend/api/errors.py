from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..domain.errors import (
    AmbiguousMoveError,
    BoardSetupError,
    DomainError,
    GameOverError,
    IllegalMoveError,
    InvalidCoordinateError,
    InvariantViolation,
    OutOfBoundsError,
    SquareEmptyError,
    SquareOccupiedError,
    StaleVersionError,
)

# Domain error to HTTP status. Anything not listed falls back to 400, and
# InvariantViolation is handled separately because it is a defect, not input.
_STATUS_BY_ERROR: dict[type[Exception], int] = {
    InvalidCoordinateError: 400,
    OutOfBoundsError: 400,
    BoardSetupError: 400,
    SquareEmptyError: 422,
    SquareOccupiedError: 422,
    IllegalMoveError: 422,
    AmbiguousMoveError: 422,
    # The game moved on or ended under the caller: a conflict, not bad input.
    GameOverError: 409,
    StaleVersionError: 409,
}


def _error_body(code: str, message: str) -> dict[str, dict[str, str]]:
    """
    Build the response body shared by every error.

    Arguments:
        code: Machine-readable error identifier.
        message: Human-readable explanation.

    Returns:
        A JSON-serialisable envelope.
    """
    return {"error": {"code": code, "message": message}}


async def handle_domain_error(_request: Request, exc: Exception) -> JSONResponse:
    """
    Map an expected domain error onto a documented HTTP response.

    Arguments:
        _request: The failing request. Unused, but required by the handler
            signature FastAPI expects.
        exc: The domain error that was raised.

    Returns:
        A JSON response carrying a stable error code and message.
    """
    status = _STATUS_BY_ERROR.get(type(exc), 400)
    return JSONResponse(
        status_code=status,
        content=_error_body(type(exc).__name__, str(exc)),
    )


async def handle_invariant_violation(_request: Request, _exc: Exception) -> JSONResponse:
    """
    Report an engine defect without leaking a traceback.

    Arguments:
        _request: The failing request. Unused, but required by the handler
            signature FastAPI expects.
        _exc: The invariant violation that was raised.

    Returns:
        A 500 response with a generic message.
    """
    return JSONResponse(
        status_code=500,
        content=_error_body("InvariantViolation", "The game engine reached an invalid state."),
    )


def register_error_handlers(app: FastAPI) -> None:
    """
    Attach the domain error handlers to an application.

    Registered most specific first, so InvariantViolation is not swallowed by
    the DomainError handler it inherits from.

    Arguments:
        app: The application to attach handlers to.
    """
    app.add_exception_handler(InvariantViolation, handle_invariant_violation)
    app.add_exception_handler(DomainError, handle_domain_error)
