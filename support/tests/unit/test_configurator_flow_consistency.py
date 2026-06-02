from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_preview_material_estimate_and_submit_are_consistent() -> None:
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
    assert patched.json()["data"]["status"] == "quote_ready"

    preview = client.get(f"/configurator/drafts/{draft_id}/quote-preview")
    assert preview.status_code == 200
    preview_payload = preview.json()["data"]

    estimate = client.get(
        f"/configurator/drafts/{draft_id}/material-consumption-estimate"
    )
    assert estimate.status_code == 200
    estimate_payload = estimate.json()["data"]

    submit = client.post(
        f"/configurator/drafts/{draft_id}/submit",
        json={},
    )
    assert submit.status_code == 200
    submit_payload = submit.json()["data"]

    assert preview_payload["total"] == submit_payload["total"]
    assert preview_payload["currency"] == submit_payload["currency"]
    assert preview_payload["material_code"] == submit_payload["human_report"]["material_code"]
    assert estimate_payload["material_ref"] == submit_payload["human_report"]["material_code"]
    assert estimate_payload["actual_material_quantity"] == 105