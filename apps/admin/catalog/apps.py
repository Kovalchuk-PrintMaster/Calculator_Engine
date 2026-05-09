# python apps/admin/manage.py check
"""
📄 Назва: CatalogConfig (AppConfig)
🧠 Призначення: під час старту імпортує моделі та адмін-модулі.
   Якщо якісь моделі ще не зареєстровані в admin — реєструє «дефолтно».
"""

from __future__ import annotations

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"
    label = "catalog"
    verbose_name = "Catalog"

    def ready(self) -> None:
        # 1) Імпорт catalog.models запускає автолоадер із п.1
        from django.apps import apps as dj_apps

        # 3) Зареєструємо все, що ще не зареєстроване (дефолтний адмін)
        from django.contrib import admin as dj_admin

        # 2) Імпорт catalog.admin запускає автолоадер із п.2
        from . import (
            admin as _catalog_admin,  # noqa: F401
            models as _catalog_models,  # noqa: F401
        )

        try:
            from import_export.admin import ImportExportModelAdmin as BaseAdmin
            from import_export.resources import modelresource_factory

            _with_ie = True
        except Exception:
            from django.contrib.admin import ModelAdmin as BaseAdmin

            _with_ie = False

        app_cfg = dj_apps.get_app_config(self.label)
        for model in app_cfg.get_models():
            if model in dj_admin.site._registry:
                continue  # уже є кастомний або раніше зареєстрований

            attrs = {
                "__module__": __name__,
                "list_display": tuple(f.name for f in model._meta.concrete_fields[:5]),
                "search_fields": tuple(
                    f.name
                    for f in model._meta.fields
                    if f.get_internal_type() in ("CharField", "TextField")
                )[:3],
            }
            if _with_ie:
                Resource = modelresource_factory(model)
                attrs["resource_classes"] = [Resource]

            AutoAdmin = type(f"{model.__name__}Admin", (BaseAdmin,), attrs)
            dj_admin.site.register(model, AutoAdmin)
