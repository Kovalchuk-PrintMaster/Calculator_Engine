from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from calculator_engine.adapters.django_bootstrap import setup_django

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


def _compute_step(*, product_template_code: str, material_code: str) -> str:
    if not product_template_code:
        return "template"
    if not material_code:
        return "material"
    return "configuration"


def _normalize_code(value: Any) -> str:
    return str(value or "").strip().lower()


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


def _serialize_draft(draft: Any) -> ConfiguratorDraftResult:
    return ConfiguratorDraftResult(
        draft_id=str(draft.public_id),
        status=draft.status,
        step=_compute_step(
            product_template_code=draft.product_template_code,
            material_code=draft.material_code,
        ),
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
    client_meta = dict(client_meta or {})
    state = dict(state or {})

    if normalized_brand_code:
        try:
            resolved = resolve_brand_runtime_defaults(
                brand_code=normalized_brand_code,
                explicit_locale=locale,
                explicit_currency=currency,
                fallback_locale=request_context_locale,
                fallback_currency=request_context_currency,
            )
            effective_locale = resolved.locale
            effective_currency = resolved.currency
            resolved_brand_code = resolved.brand_code
        except ValueError as exc:
            raise ConfiguratorDraftBrandError(str(exc)) from exc
    else:
        effective_locale = str(locale or request_context_locale).strip().lower()
        effective_currency = str(currency or request_context_currency).strip().upper()
        resolved_brand_code = ""

    draft = ConfiguratorDraft.objects.create(
        brand_code=resolved_brand_code,
        locale=effective_locale,
        currency=effective_currency,
        client_meta_json=client_meta,
        state_json=state,
    )
    return _serialize_draft(draft)


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

    return _serialize_draft(draft)


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
        draft.product_template_code = _normalize_code(product_template_code)

    if material_code is not None:
        draft.material_code = _normalize_code(material_code)

    if quantity is not None:
        if quantity <= 0:
            raise ConfiguratorDraftValidationError("Quantity must be greater than zero.")
        draft.quantity = int(quantity)

    if selected_operation_codes is not None:
        draft.selected_operation_codes_json = _normalize_ops(selected_operation_codes)

    if state is not None:
        if not isinstance(state, dict):
            raise ConfiguratorDraftValidationError("state must be an object.")
        draft.state_json = dict(state)

    draft.save(
        update_fields=[
            "product_template_code",
            "material_code",
            "quantity",
            "selected_operation_codes_json",
            "state_json",
            "updated_at",
        ]
    )
    return _serialize_draft(draft)