from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from calculator_engine.adapters.django_bootstrap import setup_django
from calculator_engine.app.services.configurator_context import (
    build_configurator_draft_quote_preview,
)
from calculator_engine.app.services.configurator_flow import (
    resolve_configurator_draft_flow_state,
)
from calculator_engine.app.services.intake_application import (
    IntakeApplicationBrandError,
    IntakeApplicationIdempotencyConflictError,
    IntakeApplicationNormalizationError,
    IntakeApplicationProcessingError,
    process_quote_intake,
)


class ConfiguratorSubmitError(ValueError):
    """Base configurator submit error."""


class ConfiguratorSubmitNotFoundError(ConfiguratorSubmitError):
    """Raised when draft does not exist."""


class ConfiguratorSubmitValidationError(ConfiguratorSubmitError):
    """Raised when draft is not ready for submit."""


@dataclass(frozen=True, slots=True)
class ConfiguratorSubmitContext:
    locale: str
    currency: str
    source_locale: str
    source_currency: str
    brand_code: str


@dataclass(frozen=True, slots=True)
class ConfiguratorDraftSubmitResult:
    draft_id: str
    job_public_id: str
    status: str
    source: str
    reused: bool
    locale: str
    currency: str
    subtotal: Decimal
    total: Decimal
    context: ConfiguratorSubmitContext
    human_report: dict
    external_report: dict


def _as_decimal(value) -> Decimal:
    return Decimal(str(value))


def _preview_route_codes(preview) -> list[str]:
    return [step.operation_code for step in preview.route]


def _human_report_route_codes(report: dict) -> list[str]:
    return [str(item.get("operation_code", "")) for item in list(report.get("route") or [])]


def _external_report_route_codes(report: dict) -> list[str]:
    return [str(item) for item in list(report.get("route_codes") or [])]


def _validate_submit_matches_preview(*, preview, result) -> None:
    human_report = dict(result.human_report or {})
    external_report = dict(result.external_report or {})

    if str(preview.currency) != str(result.currency):
        raise ConfiguratorSubmitValidationError(
            "Submit result currency does not match quote preview."
        )

    if _as_decimal(preview.subtotal) != _as_decimal(result.subtotal):
        raise ConfiguratorSubmitValidationError(
            "Submit subtotal does not match quote preview."
        )

    if _as_decimal(preview.total) != _as_decimal(result.total):
        raise ConfiguratorSubmitValidationError(
            "Submit total does not match quote preview."
        )

    if str(preview.material_code) != str(human_report.get("material_code", "")):
        raise ConfiguratorSubmitValidationError(
            "Human report material_code does not match quote preview."
        )

    if str(preview.material_code) != str(external_report.get("material_code", "")):
        raise ConfiguratorSubmitValidationError(
            "External report material_code does not match quote preview."
        )

    if int(preview.quantity) != int(human_report.get("quantity", 0)):
        raise ConfiguratorSubmitValidationError(
            "Human report quantity does not match quote preview."
        )

    if int(preview.quantity) != int(external_report.get("quantity", 0)):
        raise ConfiguratorSubmitValidationError(
            "External report quantity does not match quote preview."
        )

    preview_route_codes = _preview_route_codes(preview)
    human_route_codes = _human_report_route_codes(human_report)
    external_route_codes = _external_report_route_codes(external_report)

    if preview_route_codes != human_route_codes:
        raise ConfiguratorSubmitValidationError(
            "Human report route does not match quote preview."
        )

    if preview_route_codes != external_route_codes:
        raise ConfiguratorSubmitValidationError(
            "External report route does not match quote preview."
        )

    preview_selected_ops = list(preview.selected_operation_codes or [])
    human_selected_ops = list(human_report.get("selected_operation_codes") or [])
    external_selected_ops = list(external_report.get("selected_operation_codes") or [])

    if preview_selected_ops != human_selected_ops:
        raise ConfiguratorSubmitValidationError(
            "Human report selected operations do not match quote preview."
        )

    if preview_selected_ops != external_selected_ops:
        raise ConfiguratorSubmitValidationError(
            "External report selected operations do not match quote preview."
        )


def submit_configurator_draft(
    *,
    draft_id: str,
    source: str,
    customer_ref: str,
    request_context_locale: str,
    request_context_currency: str,
) -> ConfiguratorDraftSubmitResult:
    setup_django()

    from django.utils import timezone
    from catalog.models import ConfiguratorDraft

    try:
        draft = ConfiguratorDraft.objects.get(public_id=draft_id)
    except ConfiguratorDraft.DoesNotExist as exc:
        raise ConfiguratorSubmitNotFoundError(
            f"ConfiguratorDraft not found: {draft_id}"
        ) from exc

    template_code = draft.product_template_code or ""
    material_code = draft.material_code or ""
    quantity = draft.quantity

    flow = resolve_configurator_draft_flow_state(
        current_status=draft.status,
        product_template_code=template_code,
        material_code=material_code,
        quantity=quantity,
    )

    if not flow.can_submit:
        raise ConfiguratorSubmitValidationError(
            f"Draft is not ready for submit. Missing fields: {', '.join(flow.missing_fields)}"
        )

    preview = build_configurator_draft_quote_preview(draft_id=draft_id)

    raw_payload = {
        "source": source,
        "brand_code": draft.brand_code,
        "customer_ref": customer_ref,
        "product_template_code": template_code,
        "material_code": material_code,
        "quantity": quantity,
        "selected_operation_codes": list(draft.selected_operation_codes_json or []),
        "locale": draft.locale or request_context_locale,
        "currency": draft.currency or request_context_currency,
        "input_payload_json": {
            "_submit_origin": "configurator_draft",
            "_draft_id": str(draft.public_id),
        },
    }

    try:
        result = process_quote_intake(
            raw_payload=raw_payload,
            request_context_locale=request_context_locale,
            request_context_currency=request_context_currency,
        )
    except (
        IntakeApplicationNormalizationError,
        IntakeApplicationProcessingError,
        IntakeApplicationBrandError,
        IntakeApplicationIdempotencyConflictError,
    ) as exc:
        raise ConfiguratorSubmitValidationError(str(exc)) from exc

    _validate_submit_matches_preview(preview=preview, result=result)

    state = dict(draft.state_json or {})
    state["last_submitted_job_public_id"] = result.job_public_id
    state["last_submitted_at"] = timezone.now().isoformat()
    state["last_preview_total"] = str(preview.total)
    state["last_preview_currency"] = str(preview.currency)
    state["last_preview_route_codes"] = _preview_route_codes(preview)

    draft.status = "submitted"
    draft.state_json = state
    draft.save(update_fields=["status", "state_json", "updated_at"])

    return ConfiguratorDraftSubmitResult(
        draft_id=str(draft.public_id),
        job_public_id=result.job_public_id,
        status=result.status,
        source=result.source,
        reused=result.reused,
        locale=result.locale,
        currency=result.currency,
        subtotal=result.subtotal,
        total=result.total,
        context=ConfiguratorSubmitContext(
            locale=result.context.locale,
            currency=result.context.currency,
            source_locale=result.context.source_locale,
            source_currency=result.context.source_currency,
            brand_code=result.context.brand_code,
        ),
        human_report=result.human_report,
        external_report=result.external_report,
    )