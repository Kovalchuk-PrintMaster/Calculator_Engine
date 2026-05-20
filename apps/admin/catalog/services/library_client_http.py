from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from .library_client import (
    LibraryMaterialCategoryDTO,
    LibraryMaterialDTO,
    LibraryOperationTypeDTO,
    LibraryProductTemplateDTO,
    LibraryProductTypeDTO,
    LibraryUiBrandDTO,
)
from .library_settings import get_library_settings


class LibraryHttpClientError(RuntimeError):
    """Raised when Library HTTP client cannot fetch data."""


def _iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class LibraryHttpClient:
    def __init__(self) -> None:
        self.settings = get_library_settings()
        if not self.settings.base_url:
            raise LibraryHttpClientError("CALC_LIBRARY_BASE_URL is not configured.")

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.settings.token:
            headers["Authorization"] = f"Bearer {self.settings.token}"
        return headers

    def _get(self, path: str, *, since: datetime | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if since is not None:
            params["updated_since"] = _iso_or_none(since)

        url = f"{self.settings.base_url}{path}"

        try:
            with httpx.Client(
                timeout=self.settings.timeout_seconds,
                verify=self.settings.verify_ssl,
                headers=self._headers(),
            ) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise LibraryHttpClientError(f"Library request failed: {path} | {exc}") from exc

        if not isinstance(payload, list):
            raise LibraryHttpClientError(
                f"Library response must be a list for path {path}."
            )
        return payload

    @staticmethod
    def _parse_dt(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def fetch_material_categories(
        self,
        since: datetime | None = None,
    ) -> list[LibraryMaterialCategoryDTO]:
        items = self._get("/catalog/material-categories", since=since)
        return [
            LibraryMaterialCategoryDTO(
                external_id=item["external_id"],
                code=item["code"],
                name_i18n=item.get("name_i18n", {}),
                description_i18n=item.get("description_i18n", {}),
                form_factor=item["form_factor"],
                active=bool(item.get("active", True)),
                updated_at=self._parse_dt(item["updated_at"]),
            )
            for item in items
        ]

    def fetch_operation_types(
        self,
        since: datetime | None = None,
    ) -> list[LibraryOperationTypeDTO]:
        items = self._get("/catalog/operation-types", since=since)
        return [
            LibraryOperationTypeDTO(
                external_id=item["external_id"],
                code=item["code"],
                name_i18n=item.get("name_i18n", {}),
                description_i18n=item.get("description_i18n", {}),
                group=item["group"],
                handler_code=item["handler_code"],
                requires_setup=bool(item.get("requires_setup", False)),
                active=bool(item.get("active", True)),
                sort_order=int(item.get("sort_order", 0)),
                updated_at=self._parse_dt(item["updated_at"]),
            )
            for item in items
        ]

    def fetch_materials(
        self,
        since: datetime | None = None,
    ) -> list[LibraryMaterialDTO]:
        items = self._get("/catalog/materials", since=since)
        return [
            LibraryMaterialDTO(
                external_id=item["external_id"],
                code=item["code"],
                name_i18n=item.get("name_i18n", {}),
                category_code=item["category_code"],
                form_factor=item["form_factor"],
                density_gsm=item.get("density_gsm"),
                is_printable=bool(item.get("is_printable", False)),
                active=bool(item.get("active", True)),
                updated_at=self._parse_dt(item["updated_at"]),
            )
            for item in items
        ]

    def fetch_ui_brands(
        self,
        since: datetime | None = None,
    ) -> list[LibraryUiBrandDTO]:
        items = self._get("/catalog/ui-brands", since=since)
        return [
            LibraryUiBrandDTO(
                external_id=item["external_id"],
                code=item["code"],
                name=item["name"],
                region_code=item["region_code"],
                default_locale=item["default_locale"],
                default_currency=item["default_currency"],
                default_skin_code=item["default_skin_code"],
                active=bool(item.get("active", True)),
                updated_at=self._parse_dt(item["updated_at"]),
            )
            for item in items
        ]

    def fetch_product_types(
        self,
        since: datetime | None = None,
    ) -> list[LibraryProductTypeDTO]:
        items = self._get("/catalog/product-types", since=since)
        return [
            LibraryProductTypeDTO(
                external_id=item["external_id"],
                code=item["code"],
                name_i18n=item.get("name_i18n", {}),
                description_i18n=item.get("description_i18n", {}),
                active=bool(item.get("active", True)),
                sort_order=int(item.get("sort_order", 0)),
                updated_at=self._parse_dt(item["updated_at"]),
            )
            for item in items
        ]

    def fetch_product_templates(
        self,
        since: datetime | None = None,
    ) -> list[LibraryProductTemplateDTO]:
        items = self._get("/catalog/product-templates", since=since)
        return [
            LibraryProductTemplateDTO(
                external_id=item["external_id"],
                code=item["code"],
                name_i18n=item.get("name_i18n", {}),
                description_i18n=item.get("description_i18n", {}),
                product_type_code=item["product_type_code"],
                active=bool(item.get("active", True)),
                sort_order=int(item.get("sort_order", 0)),
                allowed_material_categories_json=item.get(
                    "allowed_material_categories_json", []
                ),
                parameter_schema_json=item.get("parameter_schema_json", {}),
                ui_schema_json=item.get("ui_schema_json", {}),
                route_profile=item.get("route_profile", "default"),
                pricing_profile=item.get("pricing_profile", "default"),
                updated_at=self._parse_dt(item["updated_at"]),
            )
            for item in items
        ]