from __future__ import annotations

from ..application.game_service import GameView
from ..domain.board import Board, Cell
from ..domain.coordinates import Coordinate
from ..domain.enums import Color, PieceKind
from ..domain.move import Move, MoveRecord
from ..domain.pieces.registry import symbol_for
from .schemas.games import (
    CellSchema,
    ColorName,
    GameResponse,
    MoveSchema,
    PieceRefSchema,
    PieceSchema,
    SquareSchema,
    TurnSchema,
)


def to_coordinate(square: SquareSchema) -> Coordinate:
    """
    Turn a square from a request into a domain coordinate.

    Arguments:
        square: The square as the client sent it.

    Returns:
        The equivalent coordinate.
    """
    return Coordinate(square.row, square.column)


def to_color(name: ColorName) -> Color:
    """
    Turn a colour name from a request into a domain colour.

    Arguments:
        name: "white" or "black".

    Returns:
        The matching colour.
    """
    return Color(name)


def game_response(view: GameView) -> GameResponse:
    """
    Describe a game for the client.

    Arguments:
        view: The game and the turns the request played.

    Returns:
        The response body.
    """
    session = view.session
    game = session.game
    human_turn = not game.status.is_over and game.side_to_move is session.human_color
    return GameResponse(
        game_id=session.game_id,
        version=game.version,
        status=game.status.name.lower(),
        end_reason=None if game.end_reason is None else game.end_reason.name.lower(),
        side_to_move=_color_name(game.side_to_move),
        human_color=_color_name(session.human_color),
        board=_board(game.position.board),
        legal_moves=[_move(move) for move in game.legal_moves()] if human_turn else [],
        turns=[_turn(record) for record in view.turns],
    )


def _color_name(color: Color) -> ColorName:
    """
    Give the wire name of a colour.

    Arguments:
        color: The colour to name.

    Returns:
        "white" or "black".
    """
    return "white" if color is Color.WHITE else "black"


def _board(board: Board) -> list[list[CellSchema]]:
    """
    Describe every square of a board.

    Arguments:
        board: The board to describe.

    Returns:
        Rows of cells, row 0 first.
    """
    return [[_cell(cell) for cell in row] for row in board.cells]


def _cell(cell: Cell) -> CellSchema:
    """
    Describe one square.

    Arguments:
        cell: The square to describe.

    Returns:
        Its terrain and its piece, if any.
    """
    piece = cell.piece
    return CellSchema(
        terrain=cell.terrain.name.lower(),
        piece=None
        if piece is None
        else PieceSchema(
            id=piece.piece_id,
            kind=piece.kind.value,
            color=_color_name(piece.color),
            symbol=symbol_for(piece),
        ),
    )


def _square(coordinate: Coordinate) -> SquareSchema:
    """
    Describe a coordinate for the client.

    Arguments:
        coordinate: The coordinate to describe.

    Returns:
        The square as row and column.
    """
    return SquareSchema(row=coordinate.row, column=coordinate.column)


def _move(move: Move) -> MoveSchema:
    """
    Describe a move for the client.

    Arguments:
        move: The move to describe.

    Returns:
        Its squares and action.
    """
    return MoveSchema(
        actor=_square(move.actor),
        origin=_square(move.origin),
        destination=_square(move.destination),
        action=move.action.name.lower(),
    )


def _turn(record: MoveRecord) -> TurnSchema:
    """
    Describe a played turn for the client.

    Arguments:
        record: The turn's record from the game history.

    Returns:
        The move and everything it caused.
    """
    return TurnSchema(
        ply=record.ply,
        side=_color_name(record.side),
        move=_move(record.move),
        captured=[_piece_ref(piece_id, kind) for piece_id, kind in record.captured],
        promoted=[_piece_ref(piece_id, kind) for piece_id, kind in record.promoted],
    )


def _piece_ref(piece_id: int, kind: PieceKind) -> PieceRefSchema:
    """
    Name a piece by identity and kind.

    Arguments:
        piece_id: The piece's identity.
        kind: Its kind.

    Returns:
        The reference.
    """
    return PieceRefSchema(id=piece_id, kind=kind.value)
