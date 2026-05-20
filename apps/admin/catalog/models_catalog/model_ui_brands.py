from django.db import models
from .model_sync_metadata import SyncMetadataMixin


class UiBrand(SyncMetadataMixin, models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)

    region_code = models.CharField(max_length=16, blank=True, default="", db_index=True)

    default_locale = models.CharField(max_length=16, default="en")
    default_currency = models.CharField(max_length=8, default="USD")

    default_skin = models.ForeignKey(
        "catalog.UiSkin",
        on_delete=models.PROTECT,
        related_name="brands",
        null=True,
        blank=True,
    )

    settings_json = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=100, db_index=True)

    class Meta:
        db_table = "ui_brands"
        verbose_name = "UI brand"
        verbose_name_plural = "UI brands"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name