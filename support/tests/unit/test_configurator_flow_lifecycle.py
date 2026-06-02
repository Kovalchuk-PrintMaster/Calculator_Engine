from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_new_draft_starts_in_draft_template_step() -> None:
    response = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["data"]["status"] == "draft"
    assert payload["data"]["step"] == "template"


def test_draft_moves_to_configuration_in_progress_after_template_selection() -> None:
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

    payload = patched.json()
    assert payload["data"]["status"] == "configuration_in_progress"
    assert payload["data"]["step"] == "material"


def test_draft_moves_to_quote_ready_when_template_material_quantity_are_present() -> None:
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

    payload = patched.json()
    assert payload["data"]["status"] == "quote_ready"
    assert payload["data"]["step"] == "quote"


def test_submitted_draft_has_submitted_status() -> None:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    ).json()
    draft_id = created["data"]["draft_id"]

    client.patch(
        f"/configurator/drafts/{draft_id}",
        json={
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
            "selected_operation_codes": ["foil"],
        },
    )

    submitted = client.post(
        f"/configurator/drafts/{draft_id}/submit",
        json={},
    )
    assert submitted.status_code == 200

    draft_response = client.get(f"/configurator/drafts/{draft_id}")
    assert draft_response.status_code == 200

    payload = draft_response.json()
    assert payload["data"]["status"] == "submitted"
    assert payload["data"]["step"] == "submitted"