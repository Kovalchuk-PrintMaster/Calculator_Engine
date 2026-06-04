from __future__ import annotations

from pathlib import Path
import importlib.util

import yaml


SCRIPT_PATH = Path("scripts/sync_blueprint_directives.py").resolve()


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "sync_blueprint_directives",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_blueprint_sync_script_exists() -> None:
    assert SCRIPT_PATH.exists()


def test_makefile_contains_blueprint_sync_directives_target() -> None:
    content = Path("Makefile").read_text(encoding="utf-8")
    assert "blueprint-sync-directives:" in content


def test_sync_blueprint_directives_imports_only_missing_active_directives(
    tmp_path,
    monkeypatch,
) -> None:
    calculator_root = tmp_path / "calculator"
    blueprint_root = tmp_path / "blueprint"

    (calculator_root / "coordination" / "prompts" / "received").mkdir(parents=True)
    (calculator_root / "coordination" / "prompts").mkdir(parents=True, exist_ok=True)

    (blueprint_root / "coordination" / "directives" / "modules" / "calculator_engine").mkdir(
        parents=True
    )

    directive_id = (
        "2026-06-03__calculator_engine__directive__final-coordination-checkpoint-and-pause-v1"
    )
    directive_filename = (
        "2026-06-03__calculator_engine__directive__final-coordination-checkpoint-and-pause-v1.md"
    )
    directive_rel_path = (
        "coordination/directives/modules/calculator_engine/" + directive_filename
    )

    (calculator_root / "coordination" / "blueprint_source.yaml").write_text(
        yaml.safe_dump(
            {
                "blueprint_source": {
                    "repo_url": "git@github.com:Kovalchuk-PrintMaster/Forprint_System_Blueprint.git",
                    "local_path": str(blueprint_root),
                    "branch": "main",
                    "global_policy_root": "coordination/global_policy",
                    "standards_root": "coordination/standards",
                    "global_directives_index": "coordination/directives/global/index.yaml",
                    "module_directives_index": "coordination/directives/modules/calculator_engine/index.yaml",
                    "module_id": "calculator_engine",
                    "status": "active",
                    "self_check_mode": "manual_first",
                }
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    (calculator_root / "coordination" / "prompts" / "index.yaml").write_text(
        yaml.safe_dump({"prompts": []}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    (blueprint_root / directive_rel_path).write_text(
        "# Final coordination checkpoint and pause\n",
        encoding="utf-8",
    )

    (blueprint_root / "coordination" / "directives" / "modules" / "calculator_engine" / "index.yaml").write_text(
        yaml.safe_dump(
            {
                "module_directives": {
                    "version": "0.1",
                    "module_id": "calculator_engine",
                    "source_module": "forprint_system_blueprint",
                    "description": "Test directives for calculator engine.",
                    "active": [
                        {
                            "directive_id": directive_id,
                            "status": "active",
                            "priority": "p0",
                            "created_at": "2026-06-03",
                            "file": directive_rel_path,
                            "related_phase": "coordination_pause",
                        }
                    ],
                    "archived": [],
                }
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    module = _load_module()
    monkeypatch.setenv("CALCULATOR_ROOT", str(calculator_root))

    result = module.main()
    assert result == 0

    imported_file = (
        calculator_root / "coordination" / "prompts" / "received" / directive_filename
    )
    assert imported_file.exists()

    prompts_index = yaml.safe_load(
        (calculator_root / "coordination" / "prompts" / "index.yaml").read_text(
            encoding="utf-8"
        )
    )
    prompts = prompts_index["prompts"]
    assert len(prompts) == 1
    assert prompts[0]["prompt_id"] == directive_id
    assert prompts[0]["directive_id"] == directive_id

    result_second = module.main()
    assert result_second == 0

    prompts_index_second = yaml.safe_load(
        (calculator_root / "coordination" / "prompts" / "index.yaml").read_text(
            encoding="utf-8"
        )
    )
    prompts_second = prompts_index_second["prompts"]
    assert len(prompts_second) == 1