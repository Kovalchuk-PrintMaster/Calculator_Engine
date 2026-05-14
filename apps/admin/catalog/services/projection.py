from __future__ import annotations

from dataclasses import dataclass

from catalog.models import Material, ProductTemplate

from .availability import get_available_operations
from .route_builder import build_route


@dataclass(frozen=True, slots=True)
class MaterialOption:
    code: str
    name: str
    category_code: str | None
    category_name: str | None
    form_factor: str
    density_gsm: int | None
    is_printable: bool


@dataclass(frozen=True, slots=True)
class ProductConfigurationPreview:
    product_template_code: str
    product_template_name: str
    material_options: list[MaterialOption]
    selected_material_code: str | None
    available_operation_codes: list[str]
    default_route_codes: list[str]


def get_material_options_for_template(
    product_template: ProductTemplate,
    *,
    only_printable: bool = True,
    locale: str = "uk",
) -> list[MaterialOption]:
    """Return materials allowed for the given product template."""

    qs = Material.objects.select_related("category").filter(active=True)

    if only_printable:
        qs = qs.filter(is_printable=True)

    allowed_categories = product_template.allowed_material_categories_json or []
    if allowed_categories:
        qs = qs.filter(category__code__in=allowed_categories)

    qs = qs.order_by("category__sort_order", "name_uk")

    result: list[MaterialOption] = []
    for material in qs:
        result.append(
            MaterialOption(
                code=material.code,
                name=material.get_name(locale),
                category_code=material.category.code if material.category else None,
                category_name=(
                    material.category.get_name(locale) if material.category else None
                ),
                form_factor=material.form_factor,
                density_gsm=material.density_gsm,
                is_printable=material.is_printable,
            )
        )

    return result


def build_product_configuration_preview(
    product_template: ProductTemplate,
    *,
    material: Material | None = None,
    locale: str = "uk",
) -> ProductConfigurationPreview:
    """Build a simple preview payload for UI/configuration layer."""

    material_options = get_material_options_for_template(
        product_template,
        locale=locale,
    )

    available_operation_codes: list[str] = []
    default_route_codes: list[str] = []
    selected_material_code: str | None = None

    if material is not None:
        selected_material_code = material.code

        available_operation_codes = [
            item.operation_type.code
            for item in get_available_operations(product_template, material)
        ]

        default_route_codes = [
            step.operation_code
            for step in build_route(product_template, material, locale=locale)
        ]

    return ProductConfigurationPreview(
        product_template_code=product_template.code,
        product_template_name=product_template.get_name(locale),
        material_options=material_options,
        selected_material_code=selected_material_code,
        available_operation_codes=available_operation_codes,
        default_route_codes=default_route_codes,
    )