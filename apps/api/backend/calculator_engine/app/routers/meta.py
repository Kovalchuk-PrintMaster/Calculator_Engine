"""Meta router."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from calculator_engine.shared.config import app_config

router = APIRouter(
    prefix="/meta",
    tags=["meta"],
    responses={404: {"description": "Not found"}},
)


class PingResponse(BaseModel):
    """Response schema for GET /meta/ping."""

    status: Literal["ok"]
    pong: Literal[1]


class InfoResponse(BaseModel):
    """Response schema for GET /meta/info."""

    service: str
    version: str
    env: str
    docs: str


@router.get("/ping", summary="Cheap ping endpoint", response_model=PingResponse)
def ping() -> PingResponse:
    """Return a tiny payload for ultra-fast liveness checks."""
    return PingResponse(status="ok", pong=1)


@router.get("/info", summary="Service info", response_model=InfoResponse)
def info() -> InfoResponse:
    """Expose minimal service metadata for humans and dashboards."""
    return InfoResponse(
        service=app_config.app_name,
        version="0.0.1",
        env=app_config.env,
        docs="/docs",
    )
