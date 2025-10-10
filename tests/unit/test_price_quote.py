"""Unit tests for POST /price/quote (stubbed pricing)."""

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_quote_minimal_payload() -> None:
    """Ensure the endpoint accepts minimal valid payload and returns a stable schema."""
    payload = {
        "product_id": "TST-001",
        "qty": 5,
        "audience": "b2c",
    }
    r = client.post("/price/quote", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"unit_price", "subtotal", "vat", "total", "lead_time_days"}
    assert isinstance(body["unit_price"], (int, float))
    assert isinstance(body["subtotal"], (int, float))
    assert isinstance(body["vat"], (int, float))
    assert isinstance(body["total"], (int, float))
    assert isinstance(body["lead_time_days"], int)


def test_quote_stub_math() -> None:
    """Validate temporary stub math: unit=10.0, subtotal=unit*qty, vat=0, total=subtotal."""
    payload = {"product_id": "TST-001", "qty": 3, "audience": "b2c"}
    r = client.post("/price/quote", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["unit_price"] == 10.0
    assert body["subtotal"] == 30.0
    assert body["vat"] == 0.0
    assert body["total"] == 30.0
    assert body["lead_time_days"] == 2


def test_quote_rejects_unsupported_audience() -> None:
    """Defensive check: unsupported audience -> 400."""
    payload = {"product_id": "TST-001", "qty": 1, "audience": "unknown"}
    r = client.post("/price/quote", json=payload)
    assert r.status_code == 400
