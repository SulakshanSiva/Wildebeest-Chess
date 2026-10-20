from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ColorName = Literal["white", "black"]


class _Request(BaseModel):
    """
    Base for request bodies: unknown fields are an error, not silently ignored.
    """

    model_config = ConfigDict(extra="forbid")


class SquareSchema(BaseModel):
    """
    One square, by zero-based row and column.

    Attributes:
        row: Row index, 0 at White's back row.
        column: Column index, 0 at the left.
    """

    model_config = ConfigDict(extra="forbid")

    row: int = Field(ge=0)
    column: int = Field(ge=0)


class CreateGameRequest(_Request):
    """
    Options for a new game.

    Attributes:
        human_color: The colour the person plays. The computer plays the other.
    """

    human_color: ColorName = "white"


class SubmitMoveRequest(_Request):
    """
    A move the person wants to make.

    Attributes:
        origin: Square of the piece to move. For a Catapult fling, the piece
            being launched.
        destination: Square it moves to.
        expected_version: The game version the move was chosen against.
        actor: Square of the piece spending the turn. Only needed if origin and
            destination alone match more than one legal move.
    """

    origin: SquareSchema
    destination: SquareSchema
    expected_version: int = Field(ge=0)
    actor: SquareSchema | None = None


class PieceSchema(BaseModel):
    """
    A piece standing on the board.

    Attributes:
        id: Stable identity, unchanged when the piece moves or is promoted.
        kind: Piece type, for example "rook".
        color: Which side owns it.
        symbol: Its board letter, uppercase for White.
    """

    id: int
    kind: str
    color: ColorName
    symbol: str


class CellSchema(BaseModel):
    """
    One square of the board.

    Attributes:
        terrain: "normal", "jet_pack" or "transporter_pad".
        piece: The piece on the square, or null when it is empty.
    """

    terrain: str
    piece: PieceSchema | None


class MoveSchema(BaseModel):
    """
    One move.

    Attributes:
        actor: Square of the piece spending the turn.
        origin: Square of the piece that moves. Differs from actor only for a
            Catapult fling, where the Catapult stays put.
        destination: Where the moving piece ends up.
        action: "move", "capture", "push", "crush" or "fling".
    """

    actor: SquareSchema
    origin: SquareSchema
    destination: SquareSchema
    action: str


class PieceRefSchema(BaseModel):
    """
    A piece named in a turn's results.

    Attributes:
        id: The piece's identity.
        kind: Its kind at that moment: for a promotion, the kind it became.
    """

    id: int
    kind: str


class RemovedPieceSchema(PieceRefSchema):
    """
    A piece removed during a turn, and why.

    Attributes:
        cause: "capture", "crush" or "fling" when the move itself removed it;
            "poison", "rampage" or "explosion" when an after-effect did.
    """

    cause: str


class TransportSchema(PieceRefSchema):
    """
    A piece a transporter pad carried during a turn.

    Attributes:
        origin: The pad it left.
        destination: The pad it arrived on.
    """

    origin: SquareSchema
    destination: SquareSchema


class TurnSchema(BaseModel):
    """
    One turn that was played, after-effects included.

    Attributes:
        ply: Zero-based index of the turn in the game.
        side: The colour that moved.
        move: The move played.
        piece: The piece that travelled from origin to destination. For a fling
            this is the flung piece, not the Catapult.
        displaced: The piece a Gorilla pushed, or null.
        captured: Every piece removed during the turn, by any cause.
        promoted: Every piece that changed kind during the turn.
        transported: Every piece a transporter pad carried during the turn.
    """

    ply: int
    side: ColorName
    move: MoveSchema
    piece: PieceRefSchema
    displaced: PieceRefSchema | None
    captured: list[RemovedPieceSchema]
    promoted: list[PieceRefSchema]
    transported: list[TransportSchema]


class GameResponse(BaseModel):
    """
    A game as it now stands, and what the request just played.

    Attributes:
        game_id: The game's identifier, used in every later request.
        version: Increases with every turn. Send it back with the next move.
        status: "active", "white_wins", "black_wins" or "draw".
        end_reason: Why the game ended, or null while it is active.
        side_to_move: The colour whose turn it is.
        human_color: The colour the person plays.
        board: Rows of cells, row 0 first.
        legal_moves: The person's legal moves, empty unless it is their turn in
            an active game.
        turns: The turns this request played, oldest first.
    """

    game_id: str
    version: int
    status: str
    end_reason: str | None
    side_to_move: ColorName
    human_color: ColorName
    board: list[list[CellSchema]]
    legal_moves: list[MoveSchema]
    turns: list[TurnSchema]
