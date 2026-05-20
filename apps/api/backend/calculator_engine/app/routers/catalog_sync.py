from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from calculator_engine.adapters.django_bootstrap import setup_django
from calculator_engine.app.api_errors import (
    ApiMeta,
    build_api_error_response,
    build_api_meta,
)

router = APIRouter(
    prefix="/catalog-sync/runs",
    tags=["catalog-sync"],
)


class CatalogSyncRunData(BaseModel):
    run_public_id: str
    source_system: str
    sync_mode: str
    status: str
    created_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    started_at: str
    finished_at: str | None


class CatalogSyncRunEnvelope(BaseModel):
    status: Literal["ok"]
    data: CatalogSyncRunData
    meta: ApiMeta


@router.get("/latest", response_model=CatalogSyncRunEnvelope, summary="Get latest catalog sync run")
def get_latest_catalog_sync_run():
    setup_django()

    from catalog.models import CatalogSyncRun

    run = CatalogSyncRun.objects.order_by("-started_at").first()
    if run is None:
        return build_api_error_response(
            status_code=404,
            code="catalog_sync_run_not_found",
            message="Catalog sync run not found.",
            detail="No catalog sync runs available.",
            retryable=False,
        )

    return CatalogSyncRunEnvelope(
        status="ok",
        data=CatalogSyncRunData(
            run_public_id=str(run.public_id),
            source_system=run.source_system,
            sync_mode=run.sync_mode,
            status=run.status,
            created_count=run.created_count,
            updated_count=run.updated_count,
            skipped_count=run.skipped_count,
            error_count=run.error_count,
            started_at=run.started_at.isoformat(),
            finished_at=run.finished_at.isoformat() if run.finished_at else None,
        ),
        meta=build_api_meta(),
    )