from __future__ import annotations

from pathlib import Path

import yaml


def test_blueprint_source_yaml_exists_and_has_required_keys() -> None:
    path = Path("coordination/blueprint_source.yaml")
    assert path.exists(), "coordination/blueprint_source.yaml is missing"

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    source = payload.get("blueprint_source") or {}

    assert source["repo_url"]
    assert source["local_path"]
    assert source["branch"] == "main"
    assert source["global_policy_root"]
    assert source["standards_root"]
    assert source["global_directives_index"]
    assert source["module_directives_index"]
    assert source["module_id"] == "calculator_engine"


def test_blueprint_self_check_script_exists() -> None:
    path = Path("scripts/check_blueprint_instructions.py")
    assert path.exists(), "Blueprint self-check script is missing"


def test_makefile_contains_blueprint_targets() -> None:
    content = Path("Makefile").read_text(encoding="utf-8")

    assert "blueprint-pull:" in content
    assert "blueprint-check:" in content
    assert "coordination-check:" in content
    assert "blueprint-sync-directives:" in content


def test_coordination_status_mentions_blueprint_pull_and_check() -> None:
    content = Path("coordination/status/current_status.md").read_text(encoding="utf-8").lower()

    assert "blueprint pull" in content
    assert "global policy" in content
    assert "standards" in content
    assert "calculator-specific directives" in content or "calculator-specific directive" in content
    assert "directive" in content


def test_coordination_report_index_mentions_blueprint_pull_self_check() -> None:
    content = Path("coordination/reports/index.yaml").read_text(encoding="utf-8")
    assert "blueprint-pull-self-check" in content