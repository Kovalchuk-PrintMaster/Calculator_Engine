from __future__ import annotations

from catalog.services.library_settings import get_library_settings


def test_get_library_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("CALC_LIBRARY_BASE_URL", raising=False)
    monkeypatch.delenv("CALC_LIBRARY_TOKEN", raising=False)
    monkeypatch.delenv("CALC_LIBRARY_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("CALC_LIBRARY_VERIFY_SSL", raising=False)

    settings = get_library_settings()

    assert settings.base_url == ""
    assert settings.token == ""
    assert settings.timeout_seconds == 10.0
    assert settings.verify_ssl is True