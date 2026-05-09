"""App entrypoint (ASGI application) for the Calculator Engine."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from calculator_engine.app.middleware import setup_middleware
from calculator_engine.app.routers.doctor import router as doctor_router
from calculator_engine.app.routers.materials import router as materials_router
from calculator_engine.app.routers.meta import router as meta_router
from calculator_engine.app.routers.price import router as price_router

app = FastAPI(
    title="Calculator Engine",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
)


class HealthResponse(BaseModel):
    """Stable response schema for /health."""

    status: Literal["ok"]
    service: str
    version: str
    docs: str


@app.get("/health", summary="Liveness probe", tags=["meta"], response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a minimal liveness payload."""
    return HealthResponse(
        status="ok",
        service="Calculator Engine",
        version=app.version or "0.0.1",
        docs="/docs",
    )


app.include_router(meta_router)
app.include_router(doctor_router)
app.include_router(price_router)
app.include_router(materials_router)

setup_middleware(app)
