from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from catalog.models import CalculationJob, Material, ProductTemplate
from catalog.services.calculation_contracts import CalculationRequest, CalculationResult
from catalog.services.pricing import PricingDataError, build_price_quote
from catalog.services.report_projection import (
    build_external_quote_response,
    build_human_quote_report,
)
from catalog.services.route_builder import RouteValidationError


class CalculationProcessingError(ValueError):
    """Raised when calculation request cannot be processed."""


class CalculationIdempotencyConflictError(CalculationProcessingError):
    """Raised when idempotency key is reused with different payload."""


VALID_CALCULATION_SOURCES = {"manual", "external"}


def build_calculation_result_from_job(job: CalculationJob) -> CalculationResult:
    human_report = job.human_report_json or {}
    external_report = job.external_report_json or {}

    return CalculationResult(
        calculation_id=str(job.public_id),
        source=job.source,
        template_code=job.product_template_code,
        material_code=job.material_code,
        quantity=job.quantity,
        selected_operation_codes=tuple(job.selected_operation_codes_json or []),
        locale=job.locale,
        currency=job.currency,
        route=human_report.get("route", []),
        lines=human_report.get("lines", []),
        subtotal=job.subtotal or Decimal("0.00"),
        total=job.total or Decimal("0.00"),
        human_report_json=human_report,
        external_report_json=external_report,
    )


def create_calculation_job(request: CalculationRequest) -> CalculationJob:
    return CalculationJob.objects.create(
        source=request.source,
        status="pending",
        brand_code=request.brand_code,
        customer_ref=request.customer_ref,
        external_order_id=request.external_order_id or "",
        external_customer_id=request.external_customer_id or "",
        idempotency_key=request.idempotency_key,
        product_template_code=request.product_template_code,
        material_code=request.material_code,
        quantity=request.quantity,
        selected_operation_codes_json=list(request.selected_operation_codes),
        locale=request.locale,
        currency=request.currency,
        request_payload_json=request.input_payload_json,
        normalized_request_json=request.to_normalized_payload(),
    )


def finalize_calculation_job(
    job: CalculationJob,
    result: CalculationResult,
) -> CalculationJob:
    job.status = "completed"
    job.subtotal = result.subtotal
    job.total = result.total
    job.human_report_json = result.human_report_json
    job.external_report_json = result.external_report_json
    job.finished_at = timezone.now()
    job.save(
        update_fields=[
            "status",
            "subtotal",
            "total",
            "human_report_json",
            "external_report_json",
            "finished_at",
        ]
    )
    return job


def fail_calculation_job(
    job: CalculationJob,
    exc: Exception,
) -> CalculationJob:
    job.status = "failed"
    job.error_message = str(exc)
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "error_message", "finished_at"])
    return job


def run_calculation_request(
    request: CalculationRequest,
    *,
    calculation_id: str | None = None,
) -> CalculationResult:
    if request.source not in VALID_CALCULATION_SOURCES:
        raise CalculationProcessingError(
            f"Unsupported calculation source: {request.source}"
        )

    if request.quantity <= 0:
        raise CalculationProcessingError("Quantity must be greater than zero.")

    try:
        template = ProductTemplate.objects.get(
            code=request.product_template_code,
            active=True,
        )
    except ProductTemplate.DoesNotExist as exc:
        raise CalculationProcessingError(
            f"ProductTemplate not found: {request.product_template_code}"
        ) from exc

    try:
        material = Material.objects.get(
            code=request.material_code,
            active=True,
        )
    except Material.DoesNotExist as exc:
        raise CalculationProcessingError(
            f"Material not found: {request.material_code}"
        ) from exc

    try:
        quote = build_price_quote(
            product_template=template,
            material=material,
            quantity=request.quantity,
            selected_operation_codes=list(request.selected_operation_codes),
            strict=True,
            locale=request.locale,
        )
    except (PricingDataError, RouteValidationError) as exc:
        raise CalculationProcessingError(str(exc)) from exc

    human_report_json = build_human_quote_report(
        request=request,
        quote=quote,
        calculation_id=calculation_id,
    )
    external_report_json = build_external_quote_response(
        request=request,
        quote=quote,
        calculation_id=calculation_id,
    )

    return CalculationResult(
        calculation_id=calculation_id,
        source=request.source,
        template_code=request.product_template_code,
        material_code=request.material_code,
        quantity=request.quantity,
        selected_operation_codes=request.selected_operation_codes,
        locale=request.locale,
        currency=request.currency,
        route=quote.route,
        lines=quote.lines,
        subtotal=quote.subtotal,
        total=quote.total,
        human_report_json=human_report_json,
        external_report_json=external_report_json,
    )


def get_reused_calculation_job(
    request: CalculationRequest,
) -> tuple[CalculationJob, CalculationResult] | None:
    if not request.idempotency_key:
        return None

    job = CalculationJob.objects.filter(
        idempotency_key=request.idempotency_key
    ).first()

    if job is None:
        return None

    expected_payload = request.to_normalized_payload()
    actual_payload = job.normalized_request_json or {}

    if actual_payload != expected_payload:
        raise CalculationIdempotencyConflictError(
            "Idempotency key already exists for different request payload."
        )

    if job.status == "completed":
        return job, build_calculation_result_from_job(job)

    if job.status == "failed":
        raise CalculationProcessingError(
            "Idempotency key belongs to failed calculation job."
        )

    raise CalculationProcessingError(
        "Idempotency key belongs to unfinished calculation job."
    )


@transaction.atomic
def process_calculation_request(
    request: CalculationRequest,
) -> tuple[CalculationJob, CalculationResult, bool]:
    reused = get_reused_calculation_job(request)
    if reused is not None:
        job, result = reused
        return job, result, True

    job = create_calculation_job(request)

    try:
        result = run_calculation_request(
            request=request,
            calculation_id=str(job.public_id),
        )
    except Exception as exc:
        fail_calculation_job(job, exc)
        raise

    finalize_calculation_job(job, result)
    return job, result, False