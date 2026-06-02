from __future__ import annotations

from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "coordination" / "blueprint_source.yaml"


def main() -> int:
    print("== Calculator Engine Blueprint Self-Check ==")

    if not CONFIG_PATH.exists():
        print(f"[FAIL] Missing config: {CONFIG_PATH}")
        return 1

    try:
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"[FAIL] Cannot parse YAML config: {exc}")
        return 1

    blueprint_source = config.get("blueprint_source") or {}
    local_path_value = blueprint_source.get("local_path")
    if not local_path_value:
        print("[FAIL] blueprint_source.local_path is missing")
        return 1

    blueprint_root = Path(str(local_path_value))
    if not blueprint_root.exists():
        print(f"[FAIL] Blueprint local path does not exist: {blueprint_root}")
        return 2

    required_relative_paths = [
        Path("coordination/global_policy"),
        Path("coordination/standards"),
        Path("coordination/directives/global/index.yaml"),
        Path("coordination/directives/modules/calculator_engine/index.yaml"),
    ]

    missing: list[Path] = []
    for rel_path in required_relative_paths:
        candidate = blueprint_root / rel_path
        if candidate.exists():
            print(f"[OK] {candidate}")
        else:
            print(f"[MISSING] {candidate}")
            missing.append(candidate)

    if missing:
        print("Blueprint self-check result: FAIL")
        return 3

    print("Blueprint self-check result: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())