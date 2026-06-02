from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from calculator_engine.adapters.django_bootstrap import setup_django
from calculator_engine.app.services.configurator_flow import (
    resolve_configurator_draft_flow_state,
)


class ConfiguratorDraftError(ValueError):
    """Base configurator draft error."""


class ConfiguratorDraftNotFoundError(ConfiguratorDraftError):
    """Raised when draft does not exist."""


class ConfiguratorDraftValidationError(ConfiguratorDraftError):
    """Raised when draft payload is invalid."""


class ConfiguratorDraftBrandError(ConfiguratorDraftError):
    """Raised when brand defaults cannot be resolved."""


@dataclass(frozen=True, slots=True)
class ConfiguratorDraftResult:
    draft_id: str
    status: str
    step: str
    brand_code: str
    product_template_code: str | None
    material_code: str | None
    quantity: int | None
    selected_operation_codes: list[str]
    locale: str
    currency: str
    client: dict[str, Any]
    state: dict[str, Any]
    created_at: str
    updated_at: str


def _normalize_code(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_optional_text(value: str | None) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _normalize_ops(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfiguratorDraftValidationError(
            "selected_operation_codes must be a list."
        )

    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        code = str(item or "").strip().lower().replace(" ", "_")
        if not code or code in seen:
            continue
        result.append(code)
        seen.add(code)
    return result


def _to_result(draft: Any) -> ConfiguratorDraftResult:
    flow = resolve_configurator_draft_flow_state(
        current_status=draft.status,
        product_template_code=draft.product_template_code,
        material_code=draft.material_code,
        quantity=draft.quantity,
    )

    return ConfiguratorDraftResult(
        draft_id=str(draft.public_id),
        status=flow.status,
        step=flow.step,
        brand_code=draft.brand_code,
        product_template_code=draft.product_template_code or None,
        material_code=draft.material_code or None,
        quantity=draft.quantity,
        selected_operation_codes=list(draft.selected_operation_codes_json or []),
        locale=draft.locale,
        currency=draft.currency,
        client=dict(draft.client_meta_json or {}),
        state=dict(draft.state_json or {}),
        created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
    )


def create_configurator_draft(
    *,
    brand_code: str,
    locale: str | None,
    currency: str | None,
    request_context_locale: str,
    request_context_currency: str,
    client_meta: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
) -> ConfiguratorDraftResult:
    setup_django()

    from catalog.models import ConfiguratorDraft
    from catalog.services import resolve_brand_runtime_defaults

    normalized_brand_code = _normalize_code(brand_code)
    normalized_locale = _normalize_optional_text(locale)
    normalized_currency = _normalize_optional_text(currency)

    try:
        runtime = resolve_brand_runtime_defaults(
            brand_code=normalized_brand_code,
            explicit_locale=normalized_locale,
            explicit_currency=normalized_currency,
            fallback_locale=request_context_locale,
            fallback_currency=request_context_currency,
        )
    except Exception as exc:
        raise ConfiguratorDraftBrandError(str(exc)) from exc

    draft = ConfiguratorDraft.objects.create(
        brand_code=runtime.brand_code,
        status="draft",
        product_template_code="",
        material_code="",
        quantity=None,
        selected_operation_codes_json=[],
        locale=runtime.locale,
        currency=runtime.currency,
        client_meta_json=dict(client_meta or {}),
        state_json=dict(state or {}),
    )

    flow = resolve_configurator_draft_flow_state(
        current_status=draft.status,
        product_template_code=draft.product_template_code,
        material_code=draft.material_code,
        quantity=draft.quantity,
    )
    draft.status = flow.status
    draft.save(update_fields=["status", "updated_at"])

    return _to_result(draft)


def get_configurator_draft(*, draft_id: str) -> ConfiguratorDraftResult:
    setup_django()

    from catalog.models import ConfiguratorDraft

    try:
        UUID(str(draft_id))
    except ValueError as exc:
        raise ConfiguratorDraftValidationError(
            f"Invalid draft_id: {draft_id}"
        ) from exc

    try:
        draft = ConfiguratorDraft.objects.get(public_id=draft_id)
    except ConfiguratorDraft.DoesNotExist as exc:
        raise ConfiguratorDraftNotFoundError(
            f"ConfiguratorDraft not found: {draft_id}"
        ) from exc

    return _to_result(draft)


def update_configurator_draft(
    *,
    draft_id: str,
    product_template_code: str | None = None,
    material_code: str | None = None,
    quantity: int | None = None,
    selected_operation_codes: list[str] | None = None,
    state: dict[str, Any] | None = None,
) -> ConfiguratorDraftResult:
    setup_django()

    from catalog.models import ConfiguratorDraft

    try:
        UUID(str(draft_id))
    except ValueError as exc:
        raise ConfiguratorDraftValidationError(
            f"Invalid draft_id: {draft_id}"
        ) from exc

    try:
        draft = ConfiguratorDraft.objects.get(public_id=draft_id)
    except ConfiguratorDraft.DoesNotExist as exc:
        raise ConfiguratorDraftNotFoundError(
            f"ConfiguratorDraft not found: {draft_id}"
        ) from exc

    if product_template_code is not None:
        draft.product_template_code = _normalize_code(product_template_code) or ""

    if material_code is not None:
        draft.material_code = _normalize_code(material_code) or ""

    if quantity is not None:
        if quantity <= 0:
            raise ConfiguratorDraftValidationError(
                "Quantity must be greater than zero."
            )
        draft.quantity = int(quantity)

    if selected_operation_codes is not None:
        draft.selected_operation_codes_json = _normalize_ops(selected_operation_codes)

    if state is not None:
        if not isinstance(state, dict):
            raise ConfiguratorDraftValidationError("state must be an object.")
        draft.state_json = dict(state)

    flow = resolve_configurator_draft_flow_state(
        current_status=draft.status,
        product_template_code=draft.product_template_code,
        material_code=draft.material_code,
        quantity=draft.quantity,
    )
    draft.status = flow.status

    draft.save(
        update_fields=[
            "product_template_code",
            "material_code",
            "quantity",
            "selected_operation_codes_json",
            "state_json",
            "status",
            "updated_at",
        ]
    )

    return _to_result(draft)