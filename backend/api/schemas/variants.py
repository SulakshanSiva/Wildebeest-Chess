from __future__ import annotations

from pydantic import BaseModel, Field


class PieceCatalogEntry(BaseModel):
    """
    One piece type as the front end sees it.

    Attributes:
        kind: Stable piece identifier.
        symbol: Layout character, uppercase for white.
        movement: Plain-language movement summary.
    """

    kind: str
    symbol: str
    movement: str


class TerrainCatalogEntry(BaseModel):
    """
    One terrain type as the front end sees it.

    Attributes:
        terrain: Stable terrain identifier.
        symbol: Layout character.
        passable: Whether a piece may occupy the square.
    """

    terrain: str
    symbol: str
    passable: bool


class VariantResponse(BaseModel):
    """
    Board dimensions, piece catalogue and rules metadata for one variant.

    Attributes:
        variant_id: Stable identifier for this ruleset.
        name: Human-readable name.
        rows: Board height.
        columns: Board width.
        first_player: Which colour moves first.
        pieces: Every piece type in the variant.
        terrain: Every terrain type in the variant.
    """

    variant_id: str
    name: str
    rows: int = Field(ge=1)
    columns: int = Field(ge=1)
    first_player: str
    pieces: list[PieceCatalogEntry]
    terrain: list[TerrainCatalogEntry]
