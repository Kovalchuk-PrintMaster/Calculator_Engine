from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from calculator_engine.app.intake_normalization import (
    IntakeNormalizationError,
    normalize_quote_intake_payload,
)
from calculator_engine.app.services.intake_request_mapper import (
    IntakeRequestMappingError,
    map_external_quote_intake_request,
)


@dataclass(frozen=True, slots=True)
class IntakeResolvedContext:
    locale: str
    currency: str
    source_locale: str
    source_currency: str
    brand_code: str


@dataclass(frozen=True, slots=True)
class IntakeQuoteSuccess:
    job_public_id: str
    status: str
    source: str
    reused: bool
    locale: str
    currency: str
    subtotal: Decimal
    total: Decimal
    context: IntakeResolvedContext
    human_report: dict
    external_report: dict


class IntakeApplicationError(ValueError):
    """Base application-layer error for intake flow."""


class IntakeApplicationNormalizationError(IntakeApplicationError):
    """Raised when raw payload cannot be normalized."""


class IntakeApplicationBrandError(IntakeApplicationError):
    """Raised when brand resolution fails."""


class IntakeApplicationProcessingError(IntakeApplicationError):
    """Raised when calculation processing fails."""


class IntakeApplicationIdempotencyConflictError(IntakeApplicationError):
    """Raised when idempotency key conflicts with existing payload."""


def process_quote_intake(
    *,
    raw_payload: dict[str, Any],
    request_context_locale: str,
    request_context_currency: str,
) -> IntakeQuoteSuccess:
    """Run full intake flow and return HTTP-agnostic result."""
    from catalog.services import (
        CalculationIdempotencyConflictError,
        CalculationProcessingError,
        CalculationRequest,
        process_calculation_request,
        resolve_brand_runtime_defaults,
    )

    try:
        mapped_request = map_external_quote_intake_request(raw_payload)
    except IntakeRequestMappingError as exc:
        raise IntakeApplicationNormalizationError(str(exc)) from exc

    try:
        normalized_payload = normalize_quote_intake_payload(
            mapped_request.processing_payload
        )
    except IntakeNormalizationError as exc:
        raise IntakeApplicationNormalizationError(str(exc)) from exc

    if normalized_payload["brand_code"]:
        try:
            resolved = resolve_brand_runtime_defaults(
                brand_code=normalized_payload["brand_code"],
                explicit_locale=normalized_payload["locale"],
                explicit_currency=normalized_payload["currency"],
                fallback_locale=request_context_locale,
                fallback_currency=request_context_currency,
            )
            effective_locale = resolved.locale
            effective_currency = resolved.currency
            resolved_brand_code = resolved.brand_code
            source_locale = resolved.source_locale
            source_currency = resolved.source_currency
        except ValueError as exc:
            raise IntakeApplicationBrandError(str(exc)) from exc
    else:
        effective_locale = normalized_payload["locale"] or request_context_locale
        effective_currency = (
            normalized_payload["currency"] or request_context_currency
        ).upper()
        resolved_brand_code = ""
        source_locale = (
            "explicit" if normalized_payload["locale"] else "request-context"
        )
        source_currency = (
            "explicit" if normalized_payload["currency"] else "request-context"
        )

    audit_payload = {
        "raw_payload": raw_payload,
        "mapped_payload": mapped_request.processing_payload,
        "request_shape": mapped_request.request_shape,
        "schema_version": mapped_request.schema_version,
        "client": mapped_request.client_meta,
        "normalized_payload": normalized_payload,
        "resolved_context": {
            "locale": effective_locale,
            "currency": effective_currency,
            "source_locale": source_locale,
            "source_currency": source_currency,
            "brand_code": resolved_brand_code,
        },
    }

    request = CalculationRequest(
        source=normalized_payload["source"],
        brand_code=normalized_payload["brand_code"],
        customer_ref=normalized_payload["customer_ref"],
        external_order_id=normalized_payload["external_order_id"],
        external_customer_id=normalized_payload["external_customer_id"],
        idempotency_key=normalized_payload["idempotency_key"],
        product_template_code=normalized_payload["product_template_code"],
        material_code=normalized_payload["material_code"],
        quantity=normalized_payload["quantity"],
        selected_operation_codes=tuple(normalized_payload["selected_operation_codes"]),
        locale=effective_locale,
        currency=effective_currency,
        input_payload_json=audit_payload,
    )

    try:
        job, result, reused = process_calculation_request(request)
    except CalculationIdempotencyConflictError as exc:
        raise IntakeApplicationIdempotencyConflictError(str(exc)) from exc
    except CalculationProcessingError as exc:
        raise IntakeApplicationProcessingError(str(exc)) from exc

    return IntakeQuoteSuccess(
        job_public_id=str(job.public_id),
        status=job.status,
        source=request.source,
        reused=reused,
        locale=result.locale,
        currency=result.currency,
        subtotal=result.subtotal,
        total=result.total,
        context=IntakeResolvedContext(
            locale=effective_locale,
            currency=effective_currency,
            source_locale=source_locale,
            source_currency=source_currency,
            brand_code=resolved_brand_code,
        ),
        human_report=result.human_report_json,
        external_report=result.external_report_json,
    )