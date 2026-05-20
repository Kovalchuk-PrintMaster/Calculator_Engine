from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_get_configurator_draft_context_for_template_step() -> None:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    ).json()

    draft_id = created["data"]["draft_id"]

    response = client.get(f"/configurator/drafts/{draft_id}/context")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["step"] == "template"
    assert payload["data"]["missing_fields"] == ["product_template_code"]
    assert payload["data"]["can_quote"] is False


def test_get_configurator_draft_context_for_material_step() -> None:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    ).json()
    draft_id = created["data"]["draft_id"]

    patched = client.patch(
        f"/configurator/drafts/{draft_id}",
        json={"product_template_code": "business_card_standard"},
    )
    assert patched.status_code == 200

    response = client.get(f"/configurator/drafts/{draft_id}/context")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["step"] == "material"
    assert payload["data"]["product_template_code"] == "business_card_standard"
    assert payload["data"]["material_options"]
    assert payload["data"]["can_select_material"] is True
    assert payload["data"]["can_quote"] is False


def test_get_configurator_draft_quote_preview() -> None:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    ).json()
    draft_id = created["data"]["draft_id"]

    patched = client.patch(
        f"/configurator/drafts/{draft_id}",
        json={
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
            "selected_operation_codes": ["foil"],
        },
    )
    assert patched.status_code == 200

    response = client.get(f"/configurator/drafts/{draft_id}/quote-preview")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["step"] == "quote"
    assert payload["data"]["currency"] == "EUR"
    assert payload["data"]["product_template_code"] == "business_card_standard"
    assert payload["data"]["material_code"] == "tintoretto_neve_300"
    assert payload["data"]["route"]
    assert payload["data"]["lines"]
    assert payload["data"]["total"] == "1100.00"


def test_get_configurator_draft_quote_preview_rejects_incomplete_draft() -> None:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    ).json()
    draft_id = created["data"]["draft_id"]

    response = client.get(f"/configurator/drafts/{draft_id}/quote-preview")
    assert response.status_code == 400

    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "draft_not_ready_for_quote"