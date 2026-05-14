from __future__ import annotations


def get_i18n_value(data: dict | None, locale: str, fallback: str = "uk") -> str:
    """Return localized value with safe fallback."""
    if not isinstance(data, dict):
        return ""

    value = data.get(locale) or data.get(fallback)
    if isinstance(value, str) and value.strip():
        return value

    for item in data.values():
        if isinstance(item, str) and item.strip():
            return item

    return ""


def make_i18n_value(
    primary_locale: str,
    primary_value: str,
    **extra: str,
) -> dict[str, str]:
    """Build normalized i18n dict."""
    result: dict[str, str] = {}

    if primary_value.strip():
        result[primary_locale] = primary_value.strip()

    for locale, value in extra.items():
        if isinstance(value, str) and value.strip():
            result[locale] = value.strip()

    return result