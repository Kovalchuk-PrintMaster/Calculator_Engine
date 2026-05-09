from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app


def test_doctor_endpoint() -> None:
    client = TestClient(app)
    r = client.get("/meta/doctor")
    assert r.status_code == 200
    payload = r.json()
    assert payload["overall"] in ("ok", "degraded", "down")
    assert isinstance(payload["checks"], list)
    assert any(c["name"] == "config" for c in payload["checks"])
