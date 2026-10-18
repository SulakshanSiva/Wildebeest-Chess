from __future__ import annotations


class DomainError(Exception):
    """
    Base class for every expected rules or validation failure.
    """


class InvariantViolation(DomainError):
    """
    Raised when the engine reaches a state its own invariants forbid.

    This is a defect rather than user error. It subclasses DomainError only so
    a single handler at the API boundary cannot leak a raw traceback.
    """


class InvalidCoordinateError(DomainError):
    """
    Raised when a coordinate is built from values that cannot name a square.
    """

    def __init__(self, row: object, column: object) -> None:
        """
        Build the error from the offending values.

        Arguments:
            row: The rejected row value.
            column: The rejected column value.
        """
        super().__init__(
            f"Coordinate ({row!r}, {column!r}) is not a pair of non-negative integers."
        )
        self.row = row
        self.column = column


class OutOfBoundsError(DomainError):
    """
    Raised when a well-formed coordinate falls outside a specific board.
    """

    def __init__(self, row: int, column: int, rows: int, columns: int) -> None:
        """
        Build the error from the square and the board it missed.

        Arguments:
            row: Row of the offending square.
            column: Column of the offending square.
            rows: Row count of the board that rejected it.
            columns: Column count of the board that rejected it.
        """
        super().__init__(f"Square ({row}, {column}) is outside a {rows}x{columns} board.")
        self.row = row
        self.column = column


class BoardSetupError(DomainError):
    """
    Raised when a starting layout cannot become a valid board.
    """


class UnknownPieceSymbolError(BoardSetupError):
    """
    Raised when a layout contains a character with no registered meaning.
    """

    def __init__(self, symbol: str, row: int, column: int) -> None:
        """
        Build the error from the unknown symbol and where it appeared.

        Arguments:
            symbol: The unrecognised layout character.
            row: Row the symbol appeared on.
            column: Column the symbol appeared on.
        """
        super().__init__(f"Unknown layout symbol {symbol!r} at ({row}, {column}).")
        self.symbol = symbol


class SquareOccupiedError(DomainError):
    """
    Raised when placing a piece on an already-occupied square.
    """

    def __init__(self, row: int, column: int) -> None:
        """
        Build the error from the occupied square.

        Arguments:
            row: Row of the occupied square.
            column: Column of the occupied square.
        """
        super().__init__(f"Square ({row}, {column}) is already occupied.")


class SquareEmptyError(DomainError):
    """
    Raised when an operation expected a piece on a square and found none.
    """

    def __init__(self, row: int, column: int) -> None:
        """
        Build the error from the empty square.

        Arguments:
            row: Row of the empty square.
            column: Column of the empty square.
        """
        super().__init__(f"Square ({row}, {column}) is empty")


class PieceNotRegisteredError(DomainError):
    """
    Raised when a piece kind has no layout symbol or no movement rule.
    """

    def __init__(self, detail: str) -> None:
        """
        Build the error from a description of what is missing.

        Arguments:
            detail: Which kinds are unregistered and in what way.
        """
        super().__init__(detail)


class IllegalMoveError(DomainError):
    """
    Raised when a submitted move is not among the legal moves of the position.
    """

    def __init__(self, detail: str) -> None:
        """
        Build the error from a description of why the move was refused.

        Arguments:
            detail: Which move was refused and why.
        """
        super().__init__(detail)


class AmbiguousMoveError(DomainError):
    """
    Raised when a request matches more than one legal move.
    """

    def __init__(self, detail: str) -> None:
        """
        Build the error from a description of the ambiguity.

        Arguments:
            detail: Which squares matched several moves.
        """
        super().__init__(detail)


class GameOverError(DomainError):
    """
    Raised when a move is submitted to a game that has already finished.
    """

    def __init__(self) -> None:
        """
        Build the error; a finished game accepts no further moves.
        """
        super().__init__("the game is over and accepts no further moves")


class StaleVersionError(DomainError):
    """
    Raised when a command was built against an older version of the game.
    """

    def __init__(self, expected: int, actual: int) -> None:
        """
        Build the error from the two versions that disagree.

        Arguments:
            expected: The version the caller believed was current.
            actual: The version the game is actually at.
        """
        super().__init__(f"expected game version {expected} but it is at {actual}")
        self.expected = expected
        self.actual = actual
