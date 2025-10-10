"""
Application middlewares: CORS and Request-ID.

Purpose:
    - Centralize middleware configuration in one place.
    - Keep `main.py` small and declarative.

Design notes:
    - CORS: enabled using settings.cors_allow_origins (dev default "*").
    - Request-ID: attaches `X-Request-ID` (uuid4) to every response; if a client
      supplies `X-Request-ID`, we trust and propagate it (useful for tracing).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from ..config.settings import settings


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach/propagate `X-Request-ID` header for every HTTP response.

    Contract:
        - If the client sends `X-Request-ID`, reuse it.
        - Otherwise generate a new UUIDv4.
        - Always set `X-Request-ID` on the response.

    Why class-based:
        Starlette's BaseHTTPMiddleware guarantees consistent execution order
        and is often more predictable than decorator-based middlewares.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def setup_middleware(app: FastAPI) -> None:
    """Register all middlewares for the ASGI app.

    Args:
        app: FastAPI application instance.
    """
    # Request-ID first (we want it on every response)
    app.add_middleware(RequestIDMiddleware)

    # CORS next: allow browser clients (Next.js site / Telegram WebApp) to call the API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
