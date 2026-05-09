"""Unit test for the /health endpoint.

Scope:
    - Ensure the endpoint responds with HTTP 200.
    - Validate the minimal stable payload shape and values.

Notes:
    fastapi.testclient.TestClient (Starlette) потребує пакету `httpx`.
"""

from fastapi.testclient import TestClient

from calculator_engine.app.main import app  # ASGI app


def test_health_returns_ok_status() -> None:
    """GET /health returns 200 and fixed 'ok' status with docs link."""
    client = TestClient(app)
    res = client.get("/health")

    assert res.status_code == 200
    payload = res.json()

    # Minimal contract we promise to external systems
    assert payload["status"] == "ok"
    assert payload["service"] == "Calculator Engine"
    assert "version" in payload and isinstance(payload["version"], str)
    assert payload["docs"] == "/docs"
