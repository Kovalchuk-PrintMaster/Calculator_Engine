from __future__ import annotations

from dataclasses import dataclass

from catalog.models import UiBrand


@dataclass(frozen=True, slots=True)
class BrandRuntimeDefaults:
    brand_code: str
    locale: str
    currency: str
    source_locale: str
    source_currency: str


def resolve_brand_runtime_defaults(
    *,
    brand_code: str,
    explicit_locale: str | None,
    explicit_currency: str | None,
    fallback_locale: str,
    fallback_currency: str,
) -> BrandRuntimeDefaults:
    """Resolve effective locale/currency for intake flow.

    Priority:
        locale: explicit -> brand default -> fallback
        currency: explicit -> brand default -> fallback
    """
    brand = UiBrand.objects.filter(code=brand_code, active=True).first()
    if brand is None:
        raise ValueError(f"UiBrand not found: {brand_code}")

    if explicit_locale:
        locale = explicit_locale
        source_locale = "explicit"
    elif brand.default_locale:
        locale = brand.default_locale
        source_locale = "brand-default"
    else:
        locale = fallback_locale
        source_locale = "request-context"

    if explicit_currency:
        currency = explicit_currency.upper()
        source_currency = "explicit"
    elif brand.default_currency:
        currency = brand.default_currency
        source_currency = "brand-default"
    else:
        currency = fallback_currency
        source_currency = "request-context"

    return BrandRuntimeDefaults(
        brand_code=brand.code,
        locale=locale,
        currency=currency,
        source_locale=source_locale,
        source_currency=source_currency,
    )