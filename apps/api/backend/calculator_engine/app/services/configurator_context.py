from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from calculator_engine.adapters.django_bootstrap import setup_django


class ConfiguratorContextError(ValueError):
    """Base configurator context error."""


class ConfiguratorContextNotFoundError(ConfiguratorContextError):
    """Raised when draft does not exist."""


class ConfiguratorContextValidationError(ConfiguratorContextError):
    """Raised when draft state is invalid."""


@dataclass(frozen=True, slots=True)
class DraftMaterialOption:
    code: str
    name: str
    category_code: str
    category_name: str
    form_factor: str
    density_gsm: int | None
    is_printable: bool


@dataclass(frozen=True, slots=True)
class DraftContextResult:
    draft_id: str
    step: str
    brand_code: str
    locale: str
    currency: str
    product_template_code: str | None
    material_code: str | None
    quantity: int | None
    selected_operation_codes: list[str]
    available_operation_codes: list[str]
    default_route_codes: list[str]
    material_options: list[DraftMaterialOption]
    missing_fields: list[str]
    can_select_material: bool
    can_quote: bool


@dataclass(frozen=True, slots=True)
class DraftQuoteRouteStep:
    operation_code: str
    operation_name: str
    operation_group: str
    handler_code: str
    sequence_order: int
    source: str


@dataclass(frozen=True, slots=True)
class DraftQuoteLine:
    code: str
    name: str
    category: str
    quantity: int
    unit: str
    unit_price: str
    total: str
    meta: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DraftQuotePreviewResult:
    draft_id: str
    step: str
    locale: str
    currency: str
    product_template_code: str
    material_code: str
    quantity: int
    selected_operation_codes: list[str]
    route: list[DraftQuoteRouteStep]
    lines: list[DraftQuoteLine]
    subtotal: Decimal
    total: Decimal


def _serialize_material_options(items: list[Any]) -> list[DraftMaterialOption]:
    result: list[DraftMaterialOption] = []
    for item in items:
        result.append(
            DraftMaterialOption(
                code=item.code,
                name=item.name,
                category_code=item.category_code,
                category_name=item.category_name,
                form_factor=item.form_factor,
                density_gsm=item.density_gsm,
                is_printable=item.is_printable,
            )
        )
    return result


def _missing_fields(*, template_code: str, material_code: str, quantity: int | None) -> list[str]:
    missing: list[str] = []
    if not template_code:
        missing.append("product_template_code")
    if template_code and not material_code:
        missing.append("material_code")
    if template_code and material_code and not quantity:
        missing.append("quantity")
    return missing


def build_configurator_draft_context(*, draft_id: str) -> DraftContextResult:
    setup_django()

    from catalog.models import ConfiguratorDraft, Material, ProductTemplate
    from catalog.services import build_product_configuration_preview

    try:
        draft = ConfiguratorDraft.objects.get(public_id=draft_id)
    except ConfiguratorDraft.DoesNotExist as exc:
        raise ConfiguratorContextNotFoundError(
            f"ConfiguratorDraft not found: {draft_id}"
        ) from exc

    template_code = draft.product_template_code or ""
    material_code = draft.material_code or ""
    quantity = draft.quantity
    selected_operation_codes = list(draft.selected_operation_codes_json or [])

    if not template_code:
        return DraftContextResult(
            draft_id=str(draft.public_id),
            step="template",
            brand_code=draft.brand_code,
            locale=draft.locale,
            currency=draft.currency,
            product_template_code=None,
            material_code=None,
            quantity=quantity,
            selected_operation_codes=selected_operation_codes,
            available_operation_codes=[],
            default_route_codes=[],
            material_options=[],
            missing_fields=["product_template_code"],
            can_select_material=False,
            can_quote=False,
        )

    template = ProductTemplate.objects.filter(code=template_code, active=True).first()
    if template is None:
        raise ConfiguratorContextValidationError(
            f"ProductTemplate not found: {template_code}"
        )

    material = None
    if material_code:
        material = Material.objects.filter(code=material_code, active=True).first()
        if material is None:
            raise ConfiguratorContextValidationError(
                f"Material not found: {material_code}"
            )

    preview = build_product_configuration_preview(
        template,
        material=material,
        locale=draft.locale,
    )

    missing = _missing_fields(
        template_code=template_code,
        material_code=material_code,
        quantity=quantity,
    )

    step = "configuration"
    if not material_code:
        step = "material"

    return DraftContextResult(
        draft_id=str(draft.public_id),
        step=step,
        brand_code=draft.brand_code,
        locale=draft.locale,
        currency=draft.currency,
        product_template_code=template_code,
        material_code=material_code or None,
        quantity=quantity,
        selected_operation_codes=selected_operation_codes,
        available_operation_codes=list(preview.available_operation_codes),
        default_route_codes=list(preview.default_route_codes),
        material_options=_serialize_material_options(list(preview.material_options)),
        missing_fields=missing,
        can_select_material=True,
        can_quote=len(missing) == 0,
    )


def build_configurator_draft_quote_preview(*, draft_id: str) -> DraftQuotePreviewResult:
    setup_django()

    from catalog.models import ConfiguratorDraft, Material, ProductTemplate
    from catalog.services import build_price_quote

    try:
        draft = ConfiguratorDraft.objects.get(public_id=draft_id)
    except ConfiguratorDraft.DoesNotExist as exc:
        raise ConfiguratorContextNotFoundError(
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
        raise ConfiguratorContextValidationError(
            f"Draft is not ready for quote preview. Missing fields: {', '.join(missing)}"
        )

    template = ProductTemplate.objects.filter(code=template_code, active=True).first()
    if template is None:
        raise ConfiguratorContextValidationError(
            f"ProductTemplate not found: {template_code}"
        )

    material = Material.objects.filter(code=material_code, active=True).first()
    if material is None:
        raise ConfiguratorContextValidationError(
            f"Material not found: {material_code}"
        )

    quote = build_price_quote(
        template,
        material,
        quantity=quantity,
        selected_operation_codes=list(draft.selected_operation_codes_json or []),
        locale=draft.locale,
    )

    return DraftQuotePreviewResult(
        draft_id=str(draft.public_id),
        step="quote",
        locale=draft.locale,
        currency=draft.currency,
        product_template_code=template_code,
        material_code=material_code,
        quantity=quantity,
        selected_operation_codes=list(draft.selected_operation_codes_json or []),
        route=[
            DraftQuoteRouteStep(
                operation_code=step.operation_code,
                operation_name=step.operation_name,
                operation_group=step.operation_group,
                handler_code=step.handler_code,
                sequence_order=step.sequence_order,
                source=step.source,
            )
            for step in quote.route
        ],
        lines=[
            DraftQuoteLine(
                code=line.code,
                name=line.name,
                category=line.category,
                quantity=line.quantity,
                unit=line.unit,
                unit_price=str(line.unit_price),
                total=str(line.total),
                meta=dict(line.meta or {}),
            )
            for line in quote.lines
        ],
        subtotal=quote.subtotal,
        total=quote.total,
    )