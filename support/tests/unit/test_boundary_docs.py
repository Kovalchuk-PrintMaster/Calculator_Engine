from __future__ import annotations

from pathlib import Path


def test_calculator_engine_boundaries_doc_contains_required_markers() -> None:
	path = Path("docs/project_config/Calculator_Engine_Boundaries.md")
	assert path.exists(), "Boundary doc is missing."

	content = path.read_text(encoding="utf-8").lower()

	assert "projection" in content
	assert "cache" in content
	assert "snapshot" in content
	assert "development-only" in content
	assert "not:" in content or "does not own" in content
	assert "material_consumption_estimate" in content
	assert "warehouse reservation" in content
	assert "canonical_truth" in content
	assert "global_registry" in content
	assert "library_replacement" in content
	assert "projection safeguard policy" in content
	assert "calculation result projections" in content
	assert "human_report" in content
	assert "external_report" in content
	assert "explicit_price_breakdown" in content
	assert "gateway replacement" in content