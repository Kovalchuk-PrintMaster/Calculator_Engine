from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


FIXTURES = Path("support/fixtures/calculator")


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_calculation_job_snapshot_fixture_shape() -> None:
    payload = _load_json("calculation_job_snapshot_example.json")

    assert payload["job_public_id"]
    assert payload["status"] == "completed"
    assert payload["product_template_code"] == "business_card_standard"
    assert payload["material_code"] == "tintoretto_neve_300"
    assert payload["currency"] == "EUR"


def test_human_report_fixture_is_calculator_projection() -> None:
    payload = _load_json("human_report_example.json")

    assert payload["report_type"] == "human_quote"
    assert payload["schema_version"] == "v1"
    assert payload["route"]
    assert payload["lines"]
    assert payload["subtotal"] == "1100.00"
    assert payload["total"] == "1100.00"


def test_external_report_fixture_is_calculator_projection() -> None:
    payload = _load_json("external_report_example.json")

    assert payload["report_type"] == "external_quote"
    assert payload["schema_version"] == "v1"
    assert payload["status"] == "ok"
    assert payload["route_codes"]
    assert payload["lines"]
    assert payload["currency"] == "EUR"


def test_price_breakdown_remains_explicit_and_separate_from_material_estimate() -> None:
    price_breakdown = _load_json("price_breakdown_example.json")
    material_estimate = _load_json("material_consumption_estimate_job_example.json")

    assert "lines" in price_breakdown
    assert "route" in price_breakdown
    assert "subtotal" in price_breakdown
    assert "total" in price_breakdown

    assert material_estimate["context_type"] == "calculation_job"
    assert "lines" not in material_estimate
    assert "route" not in material_estimate


def test_reports_endpoint_returns_calculator_owned_projection_shapes() -> None:
    create_response = client.post(
        "/intake/orders/quote",
        json={
            "source": "external",
            "brand_code": "printmaster_pl",
            "external_order_id": "SITE-ORDER-PROJECTION-1",
            "external_customer_id": "SITE-CUSTOMER-PROJECTION-1",
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
            "selected_operation_codes": ["foil"],
            "locale": "pl",
        },
    )
    assert create_response.status_code == 200
    job_public_id = create_response.json()["data"]["job_public_id"]

    report_response = client.get(f"/reports/jobs/{job_public_id}")
    assert report_response.status_code == 200

    payload = report_response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["job"]["job_public_id"] == job_public_id
    assert payload["data"]["human_report"]["report_type"] == "human_quote"
    assert payload["data"]["external_report"]["report_type"] == "external_quote"