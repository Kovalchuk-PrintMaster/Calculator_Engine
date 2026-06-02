from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_submit_matches_preview_and_saved_report() -> None:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    )
    assert created.status_code == 200
    draft_id = created.json()["data"]["draft_id"]

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
    preview_data = preview.json()["data"]

    submitted = client.post(
        f"/configurator/drafts/{draft_id}/submit",
        json={},
    )
    assert submitted.status_code == 200
    submit_data = submitted.json()["data"]

    job_public_id = submit_data["job_public_id"]

    report = client.get(f"/reports/jobs/{job_public_id}")
    assert report.status_code == 200
    report_data = report.json()["data"]

    assert preview_data["currency"] == submit_data["currency"]
    assert preview_data["subtotal"] == submit_data["subtotal"]
    assert preview_data["total"] == submit_data["total"]

    assert preview_data["material_code"] == submit_data["human_report"]["material_code"]
    assert preview_data["material_code"] == submit_data["external_report"]["material_code"]

    assert preview_data["quantity"] == submit_data["human_report"]["quantity"]
    assert preview_data["quantity"] == submit_data["external_report"]["quantity"]

    preview_route_codes = [step["operation_code"] for step in preview_data["route"]]
    human_route_codes = [
        step["operation_code"] for step in submit_data["human_report"]["route"]
    ]
    external_route_codes = list(submit_data["external_report"]["route_codes"])

    assert preview_route_codes == human_route_codes
    assert preview_route_codes == external_route_codes

    assert report_data["job"]["job_public_id"] == job_public_id
    assert report_data["job"]["total"] == submit_data["total"]
    assert report_data["human_report"]["material_code"] == preview_data["material_code"]
    assert report_data["external_report"]["material_code"] == preview_data["material_code"]


def test_submitted_draft_stores_preview_snapshot_state() -> None:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    )
    assert created.status_code == 200
    draft_id = created.json()["data"]["draft_id"]

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

    submitted = client.post(
        f"/configurator/drafts/{draft_id}/submit",
        json={},
    )
    assert submitted.status_code == 200

    draft = client.get(f"/configurator/drafts/{draft_id}")
    assert draft.status_code == 200
    state = draft.json()["data"]["state"]

    assert state["last_submitted_job_public_id"]
    assert state["last_submitted_at"]
    assert state["last_preview_total"] == "1100.00"
    assert state["last_preview_currency"] == "EUR"
    assert state["last_preview_route_codes"] == [
        "guillotine_cut",
        "digital_print",
        "foil",
    ]