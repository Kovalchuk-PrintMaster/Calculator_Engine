"""Unit tests for Request-ID middleware."""

from fastapi.testclient import TestClient

from calculator_engine.app.main import app


def test_request_id_is_generated() -> None:
    """Server generates X-Request-ID when client does not send one."""
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert "X-Request-ID" in r.headers
    assert len(r.headers["X-Request-ID"]) > 0


def test_request_id_is_propagated() -> None:
    """Server propagates client-provided X-Request-ID."""
    client = TestClient(app)
    rid = "test-fixed-id-123"
    r = client.get("/meta/ping", headers={"X-Request-ID": rid})
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID") == rid
