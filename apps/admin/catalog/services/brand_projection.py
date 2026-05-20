from __future__ import annotations

from dataclasses import dataclass

from catalog.models import UiBrand


@dataclass(frozen=True, slots=True)
class BrandTemplateOption:
    code: str
    name: str
    product_type_code: str
    product_type_name: str
    default_enabled: bool
    sort_order: int


@dataclass(frozen=True, slots=True)
class BrandCatalogProjection:
    brand_code: str
    brand_name: str
    region_code: str
    default_locale: str
    default_currency: str
    default_skin_code: str | None
    templates: list[BrandTemplateOption]


def build_brand_catalog_projection(
    brand: UiBrand,
    *,
    locale: str,
) -> BrandCatalogProjection:
    visibilities = (
        brand.template_visibilities.select_related(
            "product_template",
            "product_template__product_type",
        )
        .filter(
            active=True,
            is_visible=True,
            product_template__active=True,
            product_template__product_type__active=True,
        )
        .order_by("sort_order", "product_template__sort_order", "product_template__name_uk")
    )

    templates: list[BrandTemplateOption] = []
    for item in visibilities:
        template = item.product_template
        product_type = template.product_type

        templates.append(
            BrandTemplateOption(
                code=template.code,
                name=template.get_name(locale),
                product_type_code=product_type.code,
                product_type_name=product_type.get_name(locale),
                default_enabled=item.default_enabled,
                sort_order=item.sort_order,
            )
        )

    return BrandCatalogProjection(
        brand_code=brand.code,
        brand_name=brand.name,
        region_code=brand.region_code,
        default_locale=brand.default_locale,
        default_currency=brand.default_currency,
        default_skin_code=brand.default_skin.code if brand.default_skin else None,
        templates=templates,
    )