from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfiguratorDraftFlowState:
    status: str
    step: str
    missing_fields: list[str]
    can_select_material: bool
    can_preview_quote: bool
    can_estimate_material_consumption: bool
    can_submit: bool


def _normalize_text(value: str | None) -> str:
    return str(value or "").strip()


def _missing_fields(
    *,
    product_template_code: str | None,
    material_code: str | None,
    quantity: int | None,
) -> list[str]:
    missing: list[str] = []

    if not _normalize_text(product_template_code):
        missing.append("product_template_code")
    if _normalize_text(product_template_code) and not _normalize_text(material_code):
        missing.append("material_code")
    if _normalize_text(product_template_code) and _normalize_text(material_code) and not quantity:
        missing.append("quantity")

    return missing


def resolve_configurator_draft_flow_state(
    *,
    current_status: str | None,
    product_template_code: str | None,
    material_code: str | None,
    quantity: int | None,
) -> ConfiguratorDraftFlowState:
    normalized_status = _normalize_text(current_status).lower()

    if normalized_status == "submitted":
        return ConfiguratorDraftFlowState(
            status="submitted",
            step="submitted",
            missing_fields=[],
            can_select_material=False,
            can_preview_quote=False,
            can_estimate_material_consumption=False,
            can_submit=False,
        )

    if normalized_status == "archived":
        return ConfiguratorDraftFlowState(
            status="archived",
            step="archived",
            missing_fields=[],
            can_select_material=False,
            can_preview_quote=False,
            can_estimate_material_consumption=False,
            can_submit=False,
        )

    missing = _missing_fields(
        product_template_code=product_template_code,
        material_code=material_code,
        quantity=quantity,
    )

    if "product_template_code" in missing:
        return ConfiguratorDraftFlowState(
            status="draft",
            step="template",
            missing_fields=missing,
            can_select_material=False,
            can_preview_quote=False,
            can_estimate_material_consumption=False,
            can_submit=False,
        )

    if "material_code" in missing:
        return ConfiguratorDraftFlowState(
            status="configuration_in_progress",
            step="material",
            missing_fields=missing,
            can_select_material=True,
            can_preview_quote=False,
            can_estimate_material_consumption=False,
            can_submit=False,
        )

    if "quantity" in missing:
        return ConfiguratorDraftFlowState(
            status="configuration_in_progress",
            step="configuration",
            missing_fields=missing,
            can_select_material=True,
            can_preview_quote=False,
            can_estimate_material_consumption=False,
            can_submit=False,
        )

    return ConfiguratorDraftFlowState(
        status="quote_ready",
        step="quote",
        missing_fields=[],
        can_select_material=True,
        can_preview_quote=True,
        can_estimate_material_consumption=True,
        can_submit=True,
    )