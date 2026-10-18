from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...domain.enums import PieceKind, Terrain
from ...domain.pieces.registry import SYMBOLS, describe_kinds
from ...domain.variant import Variant
from ..schemas.variants import PieceCatalogEntry, TerrainCatalogEntry, VariantResponse

router = APIRouter(tags=["variants"])

# Only one variant exists. A mapping rather than a constant so an unknown id
# returns 404 instead of silently serving Wildebeest.
_VARIANTS: dict[str, Variant] = {Variant().variant_id: Variant()}

_SYMBOL_BY_KIND: dict[PieceKind, str] = {kind: symbol for symbol, kind in SYMBOLS.items()}


def _piece_catalog() -> list[PieceCatalogEntry]:
    """
    Describe every piece kind for the front end.

    Returns:
        One entry per piece kind, with its symbol and movement summary.
    """
    return [
        PieceCatalogEntry(kind=kind.value, symbol=_SYMBOL_BY_KIND[kind], movement=description)
        for kind, description in describe_kinds().items()
    ]


def _terrain_catalog() -> list[TerrainCatalogEntry]:
    """
    Describe every terrain type for the front end.

    Returns:
        One entry per terrain type.
    """
    return [
        TerrainCatalogEntry(
            terrain=terrain.name.lower(),
            symbol=terrain.symbol,
            passable=terrain.is_passable,
        )
        for terrain in Terrain
    ]


@router.get("/variants/{variant_id}")
async def get_variant(variant_id: str) -> VariantResponse:
    """
    Return board dimensions, the piece catalogue and rules metadata.

    Arguments:
        variant_id: Identifier of the variant to describe.

    Returns:
        The variant's metadata.
    """
    variant = _VARIANTS.get(variant_id)
    if variant is None:
        raise HTTPException(status_code=404, detail=f"unknown variant {variant_id!r}")

    board = variant.build_board()
    return VariantResponse(
        variant_id=variant.variant_id,
        name=variant.name,
        rows=board.rows,
        columns=board.columns,
        first_player=variant.first_player.value,
        pieces=_piece_catalog(),
        terrain=_terrain_catalog(),
    )
