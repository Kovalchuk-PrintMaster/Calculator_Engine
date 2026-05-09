"""Domain logic for service health/doctor checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CheckStatus = Literal["ok", "down"]
OverallStatus = Literal["ok", "degraded", "down"]


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Single doctor check result."""

    name: str
    status: CheckStatus
    detail: str


@dataclass(frozen=True, slots=True)
class DoctorResult:
    """Aggregated doctor response."""

    overall: OverallStatus
    checks: list[CheckResult]


def run_all_checks(
    *,
    app_name: str,
    postgres_dsn: str,
    redis_url: str,
) -> DoctorResult:
    """Run all lightweight service checks."""

    checks: list[CheckResult] = []

    config_ok = bool(app_name and postgres_dsn and redis_url)
    checks.append(
        CheckResult(
            name="config",
            status="ok" if config_ok else "down",
            detail="Core settings are loaded" if config_ok else "Missing required settings",
        )
    )

    postgres_ok = postgres_dsn.startswith("postgresql")
    checks.append(
        CheckResult(
            name="postgres_dsn",
            status="ok" if postgres_ok else "down",
            detail=postgres_dsn,
        )
    )

    redis_ok = redis_url.startswith("redis://")
    checks.append(
        CheckResult(
            name="redis",
            status="ok" if redis_ok else "down",
            detail=redis_url,
        )
    )

    failed = sum(1 for item in checks if item.status != "ok")

    if failed == 0:
        overall: OverallStatus = "ok"
    elif failed == len(checks):
        overall = "down"
    else:
        overall = "degraded"

    return DoctorResult(overall=overall, checks=checks)
