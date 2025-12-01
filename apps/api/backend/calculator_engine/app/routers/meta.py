"""
Meta router.

Purpose:
    Group metadata endpoints (health-like, info, version) under a single router.
    Keeps the main app entrypoint clean and enforces layered API structure.

Why:
    - Separation of concerns: routing in app/, business/domain logic elsewhere.
    - Easy discoverability for "meta" endpoints (/meta/...).
"""

from __future__ import annotations

from typing import Literal, TypedDict

from fastapi import APIRouter

from ...config.settings import settings

router = APIRouter(
    prefix="/meta",
    tags=["meta"],
    responses={404: {"description": "Not found"}},
)


class PingResponse(TypedDict):
    """Response shape for GET /meta/ping."""

    status: Literal["ok"]
    pong: Literal[1]


class InfoResponse(TypedDict):
    """Response shape for GET /meta/info."""

    service: str
    version: str
    env: str
    docs: str


@router.get("/ping", summary="Cheap ping endpoint", response_model=PingResponse)
def ping() -> PingResponse:
    """Return a tiny payload for ultra-fast liveness checks.

    Notes:
        - Intentionally does *no* I/O (no DB/Redis calls).
        - Suitable for high-frequency health probes.
    """
    return {"status": "ok", "pong": 1}


@router.get("/info", summary="Service info", response_model=InfoResponse)
def info() -> InfoResponse:
    """Expose minimal service metadata for humans and dashboards.

    Returns:
        InfoResponse: basic details like service name, version, current ENV and docs URL.
    """
    # NOTE: app version is defined in main.py; here we rely on a static value,
    #       because APIRouter does not know the FastAPI instance. Keep them in sync.
    return {
        "service": settings.app_name,
        "version": "0.0.1",
        "env": settings.env,
        "docs": "/docs",
    }
