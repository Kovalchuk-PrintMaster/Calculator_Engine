from __future__ import annotations

import pytest

from catalog.services.library_client_http import LibraryHttpClient, LibraryHttpClientError


def test_library_http_client_requires_base_url(monkeypatch) -> None:
    monkeypatch.delenv("CALC_LIBRARY_BASE_URL", raising=False)

    with pytest.raises(LibraryHttpClientError):
        LibraryHttpClient()