from django.apps import AppConfig

class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_app.catalog"
    label = "catalog"
    verbose_name = "Довідники"