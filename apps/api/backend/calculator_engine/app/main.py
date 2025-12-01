"""App entrypoint (ASGI application) for the Calculator Engine.

Призначення:
    - Експортує мінімальний FastAPI app (`app`) для Uvicorn/Hypercorn.
    - Має простий `/health` для балансувальників, моніторингу та CI.
    - Підключає модульні роутери (/meta, /price, /materials), щоб вхідна
      точка залишалася малою й читабельною.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from fastapi import FastAPI

from .middleware import setup_middleware
from .routers.meta import router as meta_router
from .routers.price import router as price_router
from .routers.materials import router as materials_router


# Створюємо ASGI-додаток на верхньому рівні (це очікує Uvicorn)
app = FastAPI(
    title="Calculator Engine",
    version="0.0.1",   # bump із релізами
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc" # альтернативна документація
)


class HealthResponse(TypedDict):
    """Схема відповіді для `/health` (легка й стабільна)."""

    status: Literal["ok"]
    service: str
    version: str
    docs: str


@app.get("/health", summary="Liveness probe", tags=["meta"])
def health() -> HealthResponse:
    """Повертає мінімальний, стабільний payload для перевірки живості.

    Чому мінімальний:
        - Health-чек викликається часто балансувальниками та моніторами.
        - Максимально швидкий та без побічних ефектів (без викликів у БД/Redis).
    """
    return {
        "status": "ok",
        "service": "Calculator Engine",
        "version": app.version or "0.0.1",
        "docs": "/docs",
    }


# --- Routers ------------------------------------------------------------------
app.include_router(meta_router)
app.include_router(price_router)
app.include_router(materials_router)  # новий базовий роутер: GET /materials

# --- Middleware ---------------------------------------------------------------
setup_middleware(app)
