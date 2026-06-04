from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import shutil

import yaml


ROOT = Path(__file__).resolve().parent.parent


def _calculator_root() -> Path:
    return Path(os.environ.get("CALCULATOR_ROOT", ROOT)).resolve()


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return payload


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _directive_id(item: dict) -> str:
    return str(item.get("directive_id") or item.get("prompt_id") or "").strip()


def _directive_file(item: dict) -> str:
    return str(
        item.get("file")
        or item.get("directive_file")
        or item.get("prompt_file")
        or ""
    ).strip()


def _is_active(item: dict) -> bool:
    return str(item.get("status", "")).strip().lower() == "active"


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _build_prompt_entry(
    *,
    directive: dict,
    local_file: Path,
) -> dict:
    directive_id = _directive_id(directive)

    entry = {
        "prompt_id": directive_id,
        "directive_id": directive_id,
        "status": "received",
        "source": "forprint_system_blueprint",
        "received_at": _today(),
        "file": local_file.as_posix(),
    }

    expected_report_id = directive.get("expected_report_id")
    related_phase = directive.get("related_phase")

    if expected_report_id:
        entry["expected_report_id"] = str(expected_report_id)
    if related_phase:
        entry["related_phase"] = str(related_phase)

    return entry


def _extract_directives(index_payload: dict) -> list[dict]:
    # New Blueprint structure:
    # module_directives:
    #   active: [...]
    module_directives = index_payload.get("module_directives")
    if isinstance(module_directives, dict):
        active = module_directives.get("active")
        if isinstance(active, list):
            return [item for item in active if isinstance(item, dict)]

    # Backward-compatible fallbacks
    directives = index_payload.get("directives")
    if isinstance(directives, list):
        return [item for item in directives if isinstance(item, dict)]

    prompts = index_payload.get("prompts")
    if isinstance(prompts, list):
        return [item for item in prompts if isinstance(item, dict)]

    return []


def main() -> int:
    calculator_root = _calculator_root()
    blueprint_config_path = calculator_root / "coordination" / "blueprint_source.yaml"
    prompts_index_path = calculator_root / "coordination" / "prompts" / "index.yaml"
    prompts_received_dir = calculator_root / "coordination" / "prompts" / "received"

    print("== Calculator Engine Blueprint Directive Sync ==")

    if not blueprint_config_path.exists():
        print(f"[FAIL] Missing config: {blueprint_config_path}")
        return 1

    config = _load_yaml(blueprint_config_path)
    blueprint_source = config.get("blueprint_source") or {}

    blueprint_root = Path(
        os.environ.get("BLUEPRINT_LOCAL_PATH_OVERRIDE")
        or str(blueprint_source.get("local_path", "")).strip()
    )
    if not blueprint_root.exists():
        print(f"[FAIL] Blueprint local path does not exist: {blueprint_root}")
        return 2

    module_index_rel = str(blueprint_source.get("module_directives_index", "")).strip()
    if not module_index_rel:
        print("[FAIL] blueprint_source.module_directives_index is missing")
        return 3

    module_index_path = blueprint_root / module_index_rel
    if not module_index_path.exists():
        print(f"[FAIL] Missing module directives index: {module_index_path}")
        return 4

    module_index = _load_yaml(module_index_path)
    directives = _extract_directives(module_index)
    if not directives:
        print("[WARN] No directive entries found in module index.")
        return 0

    local_index = _load_yaml(prompts_index_path)
    prompts = local_index.get("prompts")
    if not isinstance(prompts, list):
        prompts = []
        local_index["prompts"] = prompts

    known_ids: set[str] = set()
    for item in prompts:
        if not isinstance(item, dict):
            continue
        for key in ("prompt_id", "directive_id"):
            value = str(item.get(key, "")).strip()
            if value:
                known_ids.add(value)

    prompts_received_dir.mkdir(parents=True, exist_ok=True)

    imported: list[str] = []
    missing_sources: list[str] = []

    for directive in directives:
        directive_id = _directive_id(directive)
        source_file_raw = _directive_file(directive)

        if not directive_id:
            print("[WARN] Skipping active directive without directive_id/prompt_id")
            continue

        if not _is_active(directive):
            print(f"[SKIP] Not active: {directive_id}")
            continue

        if directive_id in known_ids:
            print(f"[SKIP] Already imported: {directive_id}")
            continue

        if not source_file_raw:
            print(f"[WARN] Skipping active directive without file: {directive_id}")
            continue

        source_path = Path(source_file_raw)
        if not source_path.is_absolute():
            source_path = blueprint_root / source_path

        if not source_path.exists():
            missing_sources.append(f"{directive_id} -> {source_path}")
            continue

        local_target = prompts_received_dir / source_path.name
        if not local_target.exists():
            shutil.copy2(source_path, local_target)

        local_file_rel = local_target.relative_to(calculator_root)
        prompts.append(
            _build_prompt_entry(
                directive=directive,
                local_file=local_file_rel,
            )
        )
        known_ids.add(directive_id)
        imported.append(directive_id)

    _write_yaml(prompts_index_path, local_index)

    if missing_sources:
        print("[FAIL] Missing directive source files:")
        for item in missing_sources:
            print(f"  - {item}")
        return 6

    if imported:
        print("Imported active directives:")
        for directive_id in imported:
            print(f"  - {directive_id}")
    else:
        print("No new active directives imported.")

    print("Blueprint directive sync result: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())