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