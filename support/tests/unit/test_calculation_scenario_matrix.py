from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)

FIXTURE_PATH = Path("support/fixtures/calculator/scenario_matrix_phase_a.json")


def _load_scenarios() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _create_ready_draft(scenario: dict) -> tuple[str, dict, dict, dict]:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": scenario["brand_code"]},
    )
    assert created.status_code == 200
    draft_id = created.json()["data"]["draft_id"]

    patched = client.patch(
        f"/configurator/drafts/{draft_id}",
        json={
            "product_template_code": scenario["product_template_code"],
            "material_code": scenario["material_code"],
            "quantity": scenario["quantity"],
            "selected_operation_codes": scenario["selected_operation_codes"],
        },
    )
    assert patched.status_code == 200
    patched_data = patched.json()["data"]
    assert patched_data["status"] == "quote_ready"
    assert patched_data["step"] == "quote"

    preview = client.get(f"/configurator/drafts/{draft_id}/quote-preview")
    assert preview.status_code == 200
    preview_data = preview.json()["data"]

    estimate = client.get(
        f"/configurator/drafts/{draft_id}/material-consumption-estimate"
    )
    assert estimate.status_code == 200
    estimate_data = estimate.json()["data"]

    submitted = client.post(
        f"/configurator/drafts/{draft_id}/submit",
        json={},
    )
    assert submitted.status_code == 200
    submit_data = submitted.json()["data"]

    return draft_id, preview_data, estimate_data, submit_data


def test_scenario_matrix_fixture_is_valid_json() -> None:
    scenarios = _load_scenarios()
    assert isinstance(scenarios, list)
    assert scenarios


def test_calculation_scenario_matrix_phase_a() -> None:
    scenarios = _load_scenarios()
    results: dict[str, dict] = {}

    for scenario in scenarios:
        _, preview, estimate, submit = _create_ready_draft(scenario)

        route_codes = [step["operation_code"] for step in preview["route"]]

        assert preview["currency"] == scenario["expected_currency"]
        assert submit["currency"] == scenario["expected_currency"]

        assert route_codes == scenario["expected_route_codes"]
        assert estimate["material_ref"] == scenario["expected_material_ref"]
        assert submit["human_report"]["material_code"] == scenario["expected_material_ref"]
        assert submit["external_report"]["material_code"] == scenario["expected_material_ref"]

        if "expected_total" in scenario:
            assert preview["total"] == scenario["expected_total"]
            assert submit["total"] == scenario["expected_total"]

        if "expected_actual_material_quantity" in scenario:
            assert (
                estimate["actual_material_quantity"]
                == scenario["expected_actual_material_quantity"]
            )

        if "min_actual_material_quantity" in scenario:
            assert (
                estimate["actual_material_quantity"]
                >= scenario["min_actual_material_quantity"]
            )

        results[scenario["code"]] = {
            "preview_total": Decimal(str(preview["total"])),
            "submit_total": Decimal(str(submit["total"])),
            "route_codes": route_codes,
        }

    for scenario in scenarios:
        compare_to = scenario.get("compare_to")
        relation = scenario.get("relation")

        if not compare_to or not relation:
            continue

        current = results[scenario["code"]]
        baseline = results[compare_to]

        if relation == "higher_total":
            assert current["preview_total"] > baseline["preview_total"]
            assert current["submit_total"] > baseline["submit_total"]
        else:
            raise AssertionError(f"Unsupported relation: {relation}")