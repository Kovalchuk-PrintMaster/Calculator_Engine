from __future__ import annotations

from decimal import Decimal
from typing import Literal,Any

from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel, Field

from calculator_engine.adapters.django_bootstrap import setup_django
from calculator_engine.app.api_errors import (
    build_api_error_response,
    build_intake_processing_error_response,
)
from calculator_engine.app.dependencies.context import get_request_context
from calculator_engine.app.services.intake_alerts import notify_intake_alert
from calculator_engine.app.services.intake_application import (
    IntakeApplicationBrandError,
    IntakeApplicationIdempotencyConflictError,
    IntakeApplicationNormalizationError,
    IntakeApplicationProcessingError,
    process_quote_intake,
)
from calculator_engine.shared.request_context import ResolvedRequestContext

from calculator_engine.app.schemas.reports import (
    ExternalQuoteReportSchema,
    HumanQuoteReportSchema,
)

from calculator_engine.app.api_errors import (
    ApiMeta,
    build_api_error_response,
    build_api_meta,
    build_intake_processing_error_response,
)
from calculator_engine.app.schemas.reports import (
    ExternalQuoteReportSchema,
    HumanQuoteReportSchema,
)
from calculator_engine.app.schemas.intake_v1 import ExternalQuoteIntakeRequestV1

router = APIRouter(
    prefix="/intake/orders",
    tags=["intake"],
    responses={404: {"description": "Not found"}},
)


class CalculationQuoteIntakeRequest(BaseModel):
    source: Literal["manual", "external"] = "external"

    brand_code: str = ""
    customer_ref: str = ""
    external_order_id: str | None = None
    external_customer_id: str | None = None
    idempotency_key: str | None = None

    product_template_code: str
    material_code: str
    quantity: int = Field(ge=1)
    selected_operation_codes: list[str] = Field(default_factory=list)

    locale: str | None = None
    currency: str | None = None

    input_payload_json: dict = Field(default_factory=dict)
    
class IntakeResolvedContextResponse(BaseModel):
    locale: str
    currency: str
    source_locale: str
    source_currency: str
    brand_code: str

    
class CalculationQuoteIntakeData(BaseModel):
    job_public_id: str
    status: str
    source: str
    reused: bool
    locale: str
    currency: str
    subtotal: Decimal
    total: Decimal
    context: IntakeResolvedContextResponse
    human_report: HumanQuoteReportSchema
    external_report: ExternalQuoteReportSchema


class CalculationQuoteIntakeEnvelope(BaseModel):
    status: Literal["ok"]
    data: CalculationQuoteIntakeData
    meta: ApiMeta


@router.post(
    "/quote",
    summary="Process automated quote intake request",
    response_model=CalculationQuoteIntakeEnvelope,
)
def intake_quote(
    payload: CalculationQuoteIntakeRequest | ExternalQuoteIntakeRequestV1 = Body(...),
    context: ResolvedRequestContext = Depends(get_request_context),
):
    
    setup_django()

    raw_payload = payload.model_dump(mode="python")
    
    try:
        result = process_quote_intake(
            raw_payload=raw_payload,
            request_context_locale=context.locale,
            request_context_currency=context.currency,
        )
    except IntakeApplicationNormalizationError as exc:
        notify_intake_alert(
            event_type="intake_normalization_error",
            detail=str(exc),
            payload=raw_payload,
        )
        return build_api_error_response(
            status_code=400,
            code="intake_normalization_error",
            message="Intake payload normalization failed.",
            detail=str(exc),
            retryable=False,
        )
    except IntakeApplicationBrandError as exc:
        notify_intake_alert(
            event_type="intake_brand_resolution_error",
            detail=str(exc),
            payload=raw_payload,
        )
        return build_intake_processing_error_response(str(exc))
    except IntakeApplicationIdempotencyConflictError as exc:
        notify_intake_alert(
            event_type="intake_idempotency_conflict",
            detail=str(exc),
            payload=raw_payload,
        )
        return build_api_error_response(
            status_code=409,
            code="idempotency_conflict",
            message="Idempotency key already exists for different request payload.",
            detail=str(exc),
            retryable=False,
        )
    except IntakeApplicationProcessingError as exc:
        notify_intake_alert(
            event_type="intake_processing_error",
            detail=str(exc),
            payload=raw_payload,
        )
        return build_intake_processing_error_response(str(exc))
    except Exception as exc:
        notify_intake_alert(
            event_type="intake_unexpected_error",
            detail=str(exc),
            payload=raw_payload,
        )
        return build_api_error_response(
            status_code=500,
            code="intake_internal_error",
            message="Internal error while processing intake request.",
            detail=str(exc),
            retryable=True,
        )

    return CalculationQuoteIntakeEnvelope(
        status="ok",
        data=CalculationQuoteIntakeData(
            job_public_id=result.job_public_id,
            status=result.status,
            source=result.source,
            reused=result.reused,
            locale=result.locale,
            currency=result.currency,
            subtotal=result.subtotal,
            total=result.total,
            context=IntakeResolvedContextResponse(
                locale=result.context.locale,
                currency=result.context.currency,
                source_locale=result.context.source_locale,
                source_currency=result.context.source_currency,
                brand_code=result.context.brand_code,
            ),
            human_report=result.human_report,
            external_report=result.external_report,
        ),
        meta=build_api_meta(),
    )