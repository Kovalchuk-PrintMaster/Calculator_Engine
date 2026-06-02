from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_create_configurator_draft_uses_brand_defaults() -> None:
    response = client.post(
        "/configurator/drafts",
        json={
            "brand_code": "printmaster_pl",
            "client": {
                "channel": "mobile",
                "device": "mobile",
            },
            "locale": None,
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["meta"]["schema_version"] == "v1"

    data = payload["data"]
    assert data["brand_code"] == "printmaster_pl"
    assert data["locale"] == "pl"
    assert data["currency"] == "EUR"
    assert data["step"] == "template"
    assert data["client"]["device"] == "mobile"


def test_get_configurator_draft() -> None:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    ).json()

    draft_id = created["data"]["draft_id"]

    response = client.get(f"/configurator/drafts/{draft_id}")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["draft_id"] == draft_id
    assert payload["data"]["step"] == "template"


def test_patch_configurator_draft_updates_fields() -> None:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    ).json()

    draft_id = created["data"]["draft_id"]

    response = client.patch(
        f"/configurator/drafts/{draft_id}",
        json={
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
            "selected_operation_codes": ["foil", "foil"],
        },
    )
    assert response.status_code == 200

    payload = response.json()
    data = payload["data"]
    assert data["product_template_code"] == "business_card_standard"
    assert data["material_code"] == "tintoretto_neve_300"
    assert data["quantity"] == 100
    assert data["selected_operation_codes"] == ["foil"]
    assert data["status"] == "quote_ready"
    assert data["step"] == "quote"


def test_create_configurator_draft_rejects_unknown_brand() -> None:
    response = client.post(
        "/configurator/drafts",
        json={"brand_code": "missing_brand"},
    )
    assert response.status_code == 400

    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "brand_not_found"


def test_patch_configurator_draft_rejects_invalid_quantity() -> None:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    ).json()

    draft_id = created["data"]["draft_id"]

    response = client.patch(
        f"/configurator/drafts/{draft_id}",
        json={"quantity": 0},
    )
    assert response.status_code == 400

    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_draft_payload"