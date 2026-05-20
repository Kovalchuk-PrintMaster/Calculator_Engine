from django.db import models

from catalog.utils import get_i18n_value
from .model_sync_metadata import SyncMetadataMixin

LAYOUT_PROFILE_CHOICES = (
    ("none", "None"),
    ("n_up", "N-up"),
    ("step_repeat", "Step & Repeat"),
    ("manual", "Manual"),
)


class ProductTemplate(SyncMetadataMixin, models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name_uk = models.CharField(max_length=255)
    name_i18n = models.JSONField(default=dict, blank=True)

    product_type = models.ForeignKey(
        "catalog.ProductType",
        on_delete=models.PROTECT,
        related_name="templates",
    )

    description = models.TextField(blank=True, default="")
    description_i18n = models.JSONField(default=dict, blank=True)

    active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=100, db_index=True)

    allowed_material_categories_json = models.JSONField(default=list, blank=True)
    parameter_schema_json = models.JSONField(default=dict, blank=True)
    ui_schema_json = models.JSONField(default=dict, blank=True)

    route_profile = models.CharField(max_length=64, blank=True, default="")
    pricing_profile = models.CharField(max_length=64, blank=True, default="")
        
    layout_profile = models.CharField(
        max_length=32,
        choices=LAYOUT_PROFILE_CHOICES,
        default="none",
    )
    allowed_layout_modes_json = models.JSONField(default=list, blank=True)
    requires_imposition = models.BooleanField(default=False)


    class Meta:
        db_table = "product_templates"
        verbose_name = "Product template"
        verbose_name_plural = "Product templates"
        ordering = ["sort_order", "name_uk"]
        indexes = [
            models.Index(fields=["product_type", "active"]),
        ]

    def get_name(self, locale: str = "uk") -> str:
        return get_i18n_value(self.name_i18n, locale) or self.name_uk

    def get_description(self, locale: str = "uk") -> str:
        return get_i18n_value(self.description_i18n, locale) or self.description

    def __str__(self) -> str:
        return self.get_name("uk")