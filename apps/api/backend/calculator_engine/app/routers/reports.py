from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from calculator_engine.adapters.django_bootstrap import setup_django
from calculator_engine.app.api_errors import (
    ApiMeta,
    build_api_error_response,
    build_api_meta,
)
from calculator_engine.app.schemas.material_consumption import (
    MaterialConsumptionEstimateSchema,
)
from calculator_engine.app.schemas.reports import (
    ExternalQuoteReportSchema,
    HumanQuoteReportSchema,
)
from calculator_engine.app.services.material_consumption_projection import (
    MaterialConsumptionProjectionNotFoundError,
    MaterialConsumptionProjectionValidationError,
    build_calculation_job_material_consumption_estimate,
)

router = APIRouter(
    prefix="/reports/jobs",
    tags=["reports"],
    responses={404: {"description": "Not found"}},
)


class CalculationJobMetaResponse(BaseModel):
    job_public_id: str
    source: str
    status: str
    brand_code: str
    customer_ref: str
    external_order_id: str
    external_customer_id: str
    product_template_code: str
    material_code: str
    quantity: int
    locale: str
    currency: str
    subtotal: Decimal | None
    total: Decimal | None
    error_message: str
    created_at: str
    finished_at: str | None


class CalculationJobReportData(BaseModel):
    job: CalculationJobMetaResponse
    human_report: HumanQuoteReportSchema
    external_report: ExternalQuoteReportSchema


class CalculationJobReportEnvelope(BaseModel):
    status: Literal["ok"]
    data: CalculationJobReportData
    meta: ApiMeta


class MaterialConsumptionEstimateEnvelope(BaseModel):
    status: Literal["ok"]
    data: MaterialConsumptionEstimateSchema
    meta: ApiMeta


def _material_consumption_estimate_to_dict(result) -> dict:
    payload = asdict(result)
    payload["waste_percent"] = str(result.waste_percent)
    return payload


def get_calculation_job_report(*, job_public_id: str):
    setup_django()

    from catalog.models import CalculationJob

    job = CalculationJob.objects.filter(public_id=UUID(job_public_id)).first()
    if job is None:
        raise CalculationJobReportNotFoundError(
            f"CalculationJob not found: {job_public_id}"
        )

    return CalculationJobReportResult(
        job=CalculationJobMetaResponse(
            job_public_id=str(job.public_id),
            source=job.source,
            status=job.status,
            brand_code=job.brand_code,
            customer_ref=job.customer_ref,
            external_order_id=job.external_order_id,
            external_customer_id=job.external_customer_id,
            product_template_code=job.product_template_code,
            material_code=job.material_code,
            quantity=job.quantity,
            locale=job.locale,
            currency=job.currency,
            subtotal=job.subtotal,
            total=job.total,
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
            finished_at=job.finished_at.isoformat() if job.finished_at else None,
        ),
        human_report=HumanQuoteReportSchema.model_validate(job.human_report_json),
        external_report=ExternalQuoteReportSchema.model_validate(job.external_report_json),
    )


class CalculationJobReportNotFoundError(ValueError):
    pass


class CalculationJobReportResult(BaseModel):
    job: CalculationJobMetaResponse
    human_report: HumanQuoteReportSchema
    external_report: ExternalQuoteReportSchema


@router.get(
    "/{job_public_id}",
    summary="Get saved calculation job report",
    response_model=CalculationJobReportEnvelope,
)
def get_job_report(job_public_id: str):
    try:
        result = get_calculation_job_report(job_public_id=job_public_id)
    except CalculationJobReportNotFoundError as exc:
        return build_api_error_response(
            status_code=404,
            code="calculation_job_not_found",
            message="Calculation job not found.",
            detail=str(exc),
            retryable=False,
        )

    return CalculationJobReportEnvelope(
        status="ok",
        data=CalculationJobReportData(
            job=result.job,
            human_report=result.human_report,
            external_report=result.external_report,
        ),
        meta=build_api_meta(),
    )


@router.get(
    "/{job_public_id}/material-consumption-estimate",
    response_model=MaterialConsumptionEstimateEnvelope,
    summary="Get calculation job material consumption estimate",
)
def get_job_material_consumption_estimate(job_public_id: str):
    try:
        result = build_calculation_job_material_consumption_estimate(
            job_public_id=job_public_id
        )
    except MaterialConsumptionProjectionValidationError as exc:
        return build_api_error_response(
            status_code=400,
            code="material_consumption_estimate_unavailable",
            message="Material consumption estimate is unavailable.",
            detail=str(exc),
            retryable=False,
        )
    except MaterialConsumptionProjectionNotFoundError as exc:
        return build_api_error_response(
            status_code=404,
            code="calculation_job_not_found",
            message="Calculation job not found.",
            detail=str(exc),
            retryable=False,
        )

    return MaterialConsumptionEstimateEnvelope(
        status="ok",
        data=MaterialConsumptionEstimateSchema.model_validate(
            _material_consumption_estimate_to_dict(result)
        ),
        meta=build_api_meta(),
    )