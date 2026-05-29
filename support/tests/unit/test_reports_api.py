from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_get_job_report_after_intake() -> None:
    create_response = client.post(
        "/intake/orders/quote",
        json={
            "source": "external",
            "brand_code": "printmaster_pl",
            "external_order_id": "SITE-ORDER-2001",
            "external_customer_id": "SITE-CUSTOMER-777",
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
            "selected_operation_codes": ["foil"],
            "locale": "pl",
        },
    )
    assert create_response.status_code == 200

    created_payload = create_response.json()
    assert created_payload["status"] == "ok"
    assert created_payload["meta"]["schema_version"] == "v1"

    job_public_id = created_payload["data"]["job_public_id"]

    report_response = client.get(f"/reports/jobs/{job_public_id}")
    assert report_response.status_code == 200

    payload = report_response.json()
    assert payload["status"] == "ok"
    assert payload["meta"]["schema_version"] == "v1"

    data = payload["data"]
    assert data["job"]["job_public_id"] == job_public_id
    assert data["job"]["status"] == "completed"
    assert data["job"]["source"] == "external"
    assert data["job"]["external_order_id"] == "SITE-ORDER-2001"
    assert data["job"]["currency"] == "EUR"
    assert data["job"]["total"] == "1100.00"

    assert data["human_report"]["currency"] == "EUR"
    assert data["external_report"]["currency"] == "EUR"
    assert data["human_report"]["report_type"] == "human_quote"
    assert data["external_report"]["report_type"] == "external_quote"
    assert data["human_report"]["schema_version"] == "v1"
    assert data["external_report"]["schema_version"] == "v1"


def test_get_job_report_returns_404_for_missing_job() -> None:
    response = client.get("/reports/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "calculation_job_not_found"
    assert "CalculationJob not found" in payload["error"]["detail"]