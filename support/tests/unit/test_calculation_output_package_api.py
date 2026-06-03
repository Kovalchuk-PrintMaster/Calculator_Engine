from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def _create_job() -> str:
    response = client.post(
        "/intake/orders/quote",
        json={
            "source": "external",
            "brand_code": "printmaster_pl",
            "external_order_id": "SITE-ORDER-PACKAGE-001",
            "external_customer_id": "SITE-CUSTOMER-PACKAGE-001",
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
            "selected_operation_codes": ["foil"],
            "locale": "pl",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["job_public_id"]


def test_get_calculation_output_package_for_job() -> None:
    job_public_id = _create_job()

    response = client.get(f"/reports/jobs/{job_public_id}/output-package")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["meta"]["schema_version"] == "v1"

    data = payload["data"]
    assert data["calculation_id"] == job_public_id

    assert data["quote_draft"]["product_template_code"] == "business_card_standard"
    assert data["quote_draft"]["material_code"] == "tintoretto_neve_300"
    assert data["quote_draft"]["total"] == "1100.00"

    assert data["order_draft"]["product_template_code"] == "business_card_standard"
    assert data["order_draft"]["material_code"] == "tintoretto_neve_300"
    assert data["order_draft"]["estimated_total"] == "1100.00"

    assert data["price_breakdown"]["total"] == "1100.00"
    assert data["material_consumption_estimate"]["actual_material_quantity"] == 105

    assert data["production_method_plan"]["method_code"] == "route_based_production_plan"
    assert data["operation_sequence"]["route_codes"] == [
        "guillotine_cut",
        "digital_print",
        "foil",
    ]


def test_get_calculation_output_package_for_missing_job() -> None:
    missing_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/reports/jobs/{missing_id}/output-package")
    assert response.status_code == 404

    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "calculation_job_not_found"