from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_external_intake_quote_uses_brand_defaults() -> None:
    response = client.post(
        "/intake/orders/quote",
        json={
            "source": "external",
            "brand_code": "printmaster_pl",
            "external_order_id": "SITE-ORDER-1001",
            "external_customer_id": "SITE-CUSTOMER-501",
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
            "selected_operation_codes": ["foil"],
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["meta"]["schema_version"] == "v1"

    data = payload["data"]
    assert data["status"] == "completed"
    assert data["source"] == "external"
    assert data["reused"] is False
    assert data["locale"] == "pl"
    assert data["currency"] == "EUR"
    assert data["total"] == "1100.00"

    assert data["context"]["locale"] == "pl"
    assert data["context"]["currency"] == "EUR"
    assert data["context"]["source_locale"] == "brand-default"
    assert data["context"]["source_currency"] == "brand-default"
    assert data["context"]["brand_code"] == "printmaster_pl"

    assert data["human_report"]["report_type"] == "human_quote"
    assert data["human_report"]["schema_version"] == "v1"
    assert data["external_report"]["report_type"] == "external_quote"
    assert data["external_report"]["schema_version"] == "v1"
    assert data["external_report"]["status"] == "ok"
    assert data["external_report"]["external_order_id"] == "SITE-ORDER-1001"


def test_external_intake_quote_explicit_values_override_brand_defaults() -> None:
    response = client.post(
        "/intake/orders/quote",
        json={
            "source": "external",
            "brand_code": "printmaster_pl",
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
            "locale": "en",
            "currency": "USD",
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["meta"]["schema_version"] == "v1"

    data = payload["data"]
    assert data["locale"] == "en"
    assert data["currency"] == "USD"
    assert data["reused"] is False
    assert data["context"]["source_locale"] == "explicit"
    assert data["context"]["source_currency"] == "explicit"


def test_external_intake_quote_reuses_existing_job_by_idempotency_key() -> None:
    idem_key = f"idem-order-{uuid4()}"

    request_payload = {
        "source": "external",
        "brand_code": "printmaster_pl",
        "external_order_id": "SITE-ORDER-IDEMP-1",
        "external_customer_id": "SITE-CUSTOMER-IDEMP-1",
        "idempotency_key": idem_key,
        "product_template_code": "business_card_standard",
        "material_code": "tintoretto_neve_300",
        "quantity": 100,
        "selected_operation_codes": ["foil"],
    }

    first = client.post("/intake/orders/quote", json=request_payload)
    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["status"] == "ok"
    assert first_payload["meta"]["schema_version"] == "v1"
    assert first_payload["data"]["reused"] is False

    second = client.post("/intake/orders/quote", json=request_payload)
    assert second.status_code == 200
    second_payload = second.json()
    assert second_payload["status"] == "ok"
    assert second_payload["meta"]["schema_version"] == "v1"

    assert second_payload["data"]["reused"] is True
    assert second_payload["data"]["job_public_id"] == first_payload["data"]["job_public_id"]
    assert second_payload["data"]["total"] == first_payload["data"]["total"]


def test_external_intake_quote_rejects_idempotency_conflict() -> None:
    idem_key = f"idem-conflict-{uuid4()}"

    first_payload = {
        "source": "external",
        "brand_code": "printmaster_pl",
        "idempotency_key": idem_key,
        "product_template_code": "business_card_standard",
        "material_code": "tintoretto_neve_300",
        "quantity": 100,
    }
    second_payload = {
        "source": "external",
        "brand_code": "printmaster_pl",
        "idempotency_key": idem_key,
        "product_template_code": "business_card_standard",
        "material_code": "tintoretto_neve_300",
        "quantity": 200,
    }

    first = client.post("/intake/orders/quote", json=first_payload)
    assert first.status_code == 200

    second = client.post("/intake/orders/quote", json=second_payload)
    assert second.status_code == 409

    payload = second.json()
    assert payload["status"] == "error"
    assert payload["meta"]["schema_version"] == "v1"
    assert payload["error"]["code"] == "idempotency_conflict"
    assert payload["error"]["retryable"] is False


def test_external_intake_quote_rejects_unknown_brand() -> None:
    response = client.post(
        "/intake/orders/quote",
        json={
            "source": "external",
            "brand_code": "missing_brand",
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
        },
    )
    assert response.status_code == 400

    payload = response.json()
    assert payload["status"] == "error"
    assert payload["meta"]["schema_version"] == "v1"
    assert payload["error"]["code"] == "brand_not_found"
    assert payload["error"]["retryable"] is False


def test_external_intake_quote_rejects_bad_material() -> None:
    response = client.post(
        "/intake/orders/quote",
        json={
            "source": "external",
            "product_template_code": "business_card_standard",
            "material_code": "missing_material",
            "quantity": 100,
        },
    )
    assert response.status_code == 400

    payload = response.json()
    assert payload["status"] == "error"
    assert payload["meta"]["schema_version"] == "v1"
    assert payload["error"]["code"] == "material_not_found"
    assert payload["error"]["retryable"] is False


def test_external_intake_quote_rejects_invalid_quantity_format() -> None:
    response = client.post(
        "/intake/orders/quote",
        json={
            "source": "external",
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": "abc",
        },
    )
    assert response.status_code == 422
    
def test_external_intake_quote_accepts_schema_v1_mobile_envelope() -> None:
    response = client.post(
        "/intake/orders/quote",
        json={
            "schema_version": "v1",
            "client": {
                "channel": "web",
                "device": "mobile",
                "platform": "ios",
                "app_version": "1.0.0",
            },
            "data": {
                "source": "external",
                "brand_code": "printmaster_pl",
                "external_order_id": "SITE-ORDER-MOBILE-1",
                "external_customer_id": "SITE-CUSTOMER-MOBILE-1",
                "product_template_code": "business_card_standard",
                "material_code": "tintoretto_neve_300",
                "quantity": 100,
                "selected_operation_codes": ["foil"],
                "locale": "pl",
            },
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["meta"]["schema_version"] == "v1"

    data = payload["data"]
    assert data["status"] == "completed"
    assert data["source"] == "external"
    assert data["locale"] == "pl"
    assert data["currency"] == "EUR"
    assert data["human_report"]["schema_version"] == "v1"
    assert data["external_report"]["schema_version"] == "v1"


def test_external_intake_quote_rejects_unknown_schema_version() -> None:
    response = client.post(
        "/intake/orders/quote",
        json={
            "schema_version": "v2",
            "client": {
                "channel": "mobile",
                "device": "mobile",
            },
            "data": {
                "source": "external",
                "product_template_code": "business_card_standard",
                "material_code": "tintoretto_neve_300",
                "quantity": 100,
            },
        },
    )
    assert response.status_code == 400

    payload = response.json()
    assert payload["status"] == "error"
    assert payload["meta"]["schema_version"] == "v1"
    assert payload["error"]["code"] == "intake_normalization_error"