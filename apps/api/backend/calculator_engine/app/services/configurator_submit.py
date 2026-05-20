from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from calculator_engine.adapters.django_bootstrap import setup_django
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


def _missing_fields(*, template_code: str, material_code: str, quantity: int | None) -> list[str]:
    missing: list[str] = []
    if not template_code:
        missing.append("product_template_code")
    if template_code and not material_code:
        missing.append("material_code")
    if template_code and material_code and not quantity:
        missing.append("quantity")
    return missing


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

    missing = _missing_fields(
        template_code=template_code,
        material_code=material_code,
        quantity=quantity,
    )
    if missing:
        raise ConfiguratorSubmitValidationError(
            f"Draft is not ready for submit. Missing fields: {', '.join(missing)}"
        )

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

    state = dict(draft.state_json or {})
    state["last_submitted_job_public_id"] = result.job_public_id
    state["last_submitted_at"] = timezone.now().isoformat()

    draft.status = ConfiguratorDraft.Status.SUBMITTED
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