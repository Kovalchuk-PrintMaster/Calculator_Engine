"""
Middleware-шар для додаткових перехоплень:
    - X-Request-ID: прийняти з клієнта або згенерувати; покласти у контекст;
      повернути у відповідь для трасування.

Розширення:
    - Можна додати інші cross-cutting concerns (rate limit, CORS, тощо).
"""

from __future__ import annotations

import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from calculator_engine.shared.request_context import REQUEST_ID_VAR


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Забезпечує наявність X-Request-ID:
        - Приймає з заголовків або генерує новий UUID4.
        - Кладе значення у контекст (ContextVar) для логів.
        - Додає X-Request-ID у відповідь.
    """

    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(self.header_name)
        rid = incoming or str(uuid.uuid4())

        # зберігаємо у контексті для логів
        token = REQUEST_ID_VAR.set(rid)
        try:
            response = await call_next(request)
        finally:
            # відновлюємо попереднє значення, щоб не протікало між запитами
            REQUEST_ID_VAR.reset(token)

        # повертаємо заголовок клієнту
        response.headers[self.header_name] = rid
        return response


def setup_middleware(app) -> None:
    """
    Підключаємо всі middleware одного місця (точка входу main.py).
    """
    app.add_middleware(RequestIdMiddleware)
