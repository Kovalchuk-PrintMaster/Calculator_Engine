"""
App entrypoint (ASGI application) for the Calculator Engine.

Purpose:
    - Expose a minimal FastAPI app instance (`app`) for ASGI servers (Uvicorn, Hypercorn).
    - Provide a simple `/health` endpoint used by load balancers, monitoring and CI checks.
    - Include modular routers (e.g., /meta, /price) to keep the entrypoint small.

Owner: Core Platform Team   Last updated: 2025-10-09
"""

from __future__ import annotations

from typing import Literal, TypedDict

from fastapi import FastAPI

# Keep imports single and at the top-level. Do not include routers before `app` is created.
from .middleware import setup_middleware
from .routers.meta import router as meta_router
from .routers.price import router as price_router

# Create the ASGI app early (Uvicorn expects a top-level `app`).
app = FastAPI(
    title="Calculator Engine",
    version="0.0.1",  # bump with releases
    docs_url="/docs",  # interactive Swagger UI
    redoc_url="/redoc",  # alternative docs UI
)


class HealthResponse(TypedDict):
    """
    HTTP response schema for `/health`.

    Using TypedDict instead of a Pydantic model keeps the endpoint lightweight.
    We reserve Pydantic models for business payloads (quotes, orders, etc.).
    """

    status: Literal["ok"]
    service: str
    version: str
    docs: str


@app.get("/health", summary="Liveness probe", tags=["meta"])
def health() -> HealthResponse:
    """Return a minimal, stable payload proving the service is alive.

    Why minimal:
        - Health checks are called frequently by load balancers and uptime monitors.
        - Keep it fast and side-effect free (no DB/Redis calls here).
    """
    return {
        "status": "ok",
        "service": "Calculator Engine",
        "version": app.version or "0.0.1",
        "docs": "/docs",
    }


# --- Routers ------------------------------------------------------------------
# Include routers only after the app is created; include each router exactly once.
app.include_router(meta_router)
app.include_router(price_router)

# --- Middleware ---------------------------------------------------------------
# Register middlewares at the end to keep `main.py` wiring clear and ordered.
setup_middleware(app)
