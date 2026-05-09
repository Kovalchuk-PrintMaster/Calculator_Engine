"""Doctor router."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from calculator_engine.domain.doctor.checks import run_all_checks
from calculator_engine.shared.config import app_config

router = APIRouter(
    prefix="/meta",
    tags=["meta"],
    responses={404: {"description": "Not found"}},
)


class DoctorCheckResponse(BaseModel):
    """Single doctor check item."""

    name: str
    status: Literal["ok", "down"]
    detail: str


class DoctorResponse(BaseModel):
    """Response schema for GET /meta/doctor."""

    overall: Literal["ok", "degraded", "down"]
    checks: list[DoctorCheckResponse]


@router.get("/doctor", summary="Doctor endpoint", response_model=DoctorResponse)
def doctor() -> DoctorResponse:
    """Return lightweight diagnostic checks for the service."""
    result = run_all_checks(
        app_name=app_config.app_name,
        postgres_dsn=app_config.postgres_dsn,
        redis_url=app_config.redis_url,
    )

    return DoctorResponse(
        overall=result.overall,
        checks=[
            DoctorCheckResponse(
                name=item.name,
                status=item.status,
                detail=item.detail,
            )
            for item in result.checks
        ],
    )
