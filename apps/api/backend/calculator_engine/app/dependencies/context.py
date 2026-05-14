from __future__ import annotations

from fastapi import Header, Query

from calculator_engine.shared.request_context import (
    ResolvedRequestContext,
    resolve_request_context,
)


def get_request_context(
    locale: str | None = Query(default=None),
    currency: str | None = Query(default=None),
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    cf_ipcountry: str | None = Header(default=None, alias="CF-IPCountry"),
    x_country_code: str | None = Header(default=None, alias="X-Country-Code"),
    x_geo_country: str | None = Header(default=None, alias="X-Geo-Country"),
) -> ResolvedRequestContext:
    country_code = x_country_code or cf_ipcountry or x_geo_country

    return resolve_request_context(
        explicit_locale=locale,
        explicit_currency=currency,
        accept_language=accept_language,
        country_code=country_code,
    )