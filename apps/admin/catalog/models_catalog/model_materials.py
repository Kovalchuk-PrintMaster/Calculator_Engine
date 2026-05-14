from django.db import models

from catalog.utils import get_i18n_value

from .model_material_categories import FormFactor


class Material(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name_uk = models.CharField(max_length=255)
    name_i18n = models.JSONField(default=dict, blank=True)

    category = models.ForeignKey(
        "catalog.MaterialCategory",
        on_delete=models.PROTECT,
        related_name="materials",
        null=True,
        blank=True,
    )

    form_factor = models.CharField(
        max_length=16,
        choices=FormFactor.choices,
        default=FormFactor.SHEET,
        db_index=True,
    )

    density_gsm = models.PositiveIntegerField(null=True, blank=True)
    thickness_um = models.PositiveIntegerField(null=True, blank=True)
    width_mm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height_mm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    vendor_name = models.CharField(max_length=255, blank=True, default="")
    is_printable = models.BooleanField(default=True, db_index=True)
    active = models.BooleanField(default=True, db_index=True)

    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "materials"
        verbose_name = "Material"
        verbose_name_plural = "Materials"
        ordering = ["name_uk"]
        indexes = [
            models.Index(fields=["category", "active"]),
            models.Index(fields=["form_factor", "active"]),
        ]

    def get_name(self, locale: str = "uk") -> str:
        return get_i18n_value(self.name_i18n, locale) or self.name_uk

    def __str__(self) -> str:
        return self.get_name("uk")