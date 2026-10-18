from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """
    Liveness payload.

    Attributes:
        status: Always "ok" when the process is serving.
    """

    status: str


@router.get("/healthz")
async def healthz() -> HealthResponse:
    """
    Report that the process is alive.

    Deliberately depends on no game state, so it stays meaningful whether or
    not any games exist.

    Returns:
        A payload with status "ok".
    """
    return HealthResponse(status="ok")
