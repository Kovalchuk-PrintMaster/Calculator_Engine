"""Unit tests for /meta router endpoints."""

from fastapi.testclient import TestClient

from calculator_engine.app.main import app


def test_meta_ping() -> None:
    """GET /meta/ping returns a tiny, stable payload."""
    client = TestClient(app)
    r = client.get("/meta/ping")
    assert r.status_code == 200
    body = r.json()
    assert body == {"status": "ok", "pong": 1}


def test_meta_info() -> None:
    """GET /meta/info exposes service name, version, env and docs link."""
    client = TestClient(app)
    r = client.get("/meta/info")
    assert r.status_code == 200
    body = r.json()
    assert "service" in body and isinstance(body["service"], str)
    assert "version" in body and isinstance(body["version"], str)
    assert "env" in body and isinstance(body["env"], str)
    assert body["docs"] == "/docs"
