from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

REQUEST_ID_VAR: ContextVar[str] = ContextVar("request_id", default="-")

EUROPEAN_COUNTRY_CODES = {
    "AL", "AD", "AT", "BE", "BA", "BG", "HR", "CY", "CZ", "DK", "EE", "FI",
    "FR", "DE", "GR", "HU", "IS", "IE", "IT", "LV", "LI", "LT", "LU", "MT",
    "MD", "MC", "ME", "NL", "MK", "NO", "PL", "PT", "RO", "SM", "RS", "SK",
    "SI", "ES", "SE", "CH", "UA", "GB", "VA",
}

COUNTRY_TO_LOCALE = {
    "UA": "uk",
    "PL": "pl",
    "DE": "de",
    "FR": "fr",
    "ES": "es",
    "IT": "it",
    "GB": "en",
    "US": "en",
}


@dataclass(frozen=True, slots=True)
class ResolvedRequestContext:
    locale: str
    currency: str
    country_code: str | None
    source_locale: str
    source_currency: str


def normalize_locale(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().lower()
    if not value:
        return None

    primary = value.split(",")[0].split(";")[0].strip()
    if not primary:
        return None

    return primary.split("-")[0]


def resolve_currency_by_country(country_code: str | None) -> str:
    if not country_code:
        return "USD"
    return "EUR" if country_code.upper() in EUROPEAN_COUNTRY_CODES else "USD"


def resolve_locale_by_country(country_code: str | None) -> str:
    if not country_code:
        return "en"
    return COUNTRY_TO_LOCALE.get(country_code.upper(), "en")


def resolve_request_context(
    *,
    explicit_locale: str | None = None,
    explicit_currency: str | None = None,
    accept_language: str | None = None,
    country_code: str | None = None,
) -> ResolvedRequestContext:
    locale = normalize_locale(explicit_locale)
    currency = explicit_currency.upper() if explicit_currency else None
    country_code = country_code.upper() if country_code else None

    if locale:
        source_locale = "explicit"
    else:
        locale = normalize_locale(accept_language)
        if locale:
            source_locale = "accept-language"
        else:
            locale = resolve_locale_by_country(country_code)
            source_locale = "geoip-default"

    if currency:
        source_currency = "explicit"
    else:
        currency = resolve_currency_by_country(country_code)
        source_currency = "geoip-default"

    return ResolvedRequestContext(
        locale=locale or "en",
        currency=currency or "USD",
        country_code=country_code,
        source_locale=source_locale,
        source_currency=source_currency,
    )


__all__ = [
    "REQUEST_ID_VAR",
    "ResolvedRequestContext",
    "normalize_locale",
    "resolve_currency_by_country",
    "resolve_locale_by_country",
    "resolve_request_context",
]
