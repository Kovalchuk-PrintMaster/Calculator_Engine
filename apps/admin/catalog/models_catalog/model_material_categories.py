from django.db import models

from catalog.utils import get_i18n_value


class FormFactor(models.TextChoices):
    SHEET = "sheet", "Sheet"
    ROLL = "roll", "Roll"
    OTHER = "other", "Other"


class MaterialCategory(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name_uk = models.CharField(max_length=255)
    name_i18n = models.JSONField(default=dict, blank=True)

    description = models.TextField(blank=True, default="")
    description_i18n = models.JSONField(default=dict, blank=True)

    form_factor = models.CharField(
        max_length=16,
        choices=FormFactor.choices,
        default=FormFactor.SHEET,
        db_index=True,
    )
    active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=100, db_index=True)

    class Meta:
        db_table = "material_categories"
        verbose_name = "Material category"
        verbose_name_plural = "Material categories"
        ordering = ["sort_order", "name_uk"]

    def get_name(self, locale: str = "uk") -> str:
        return get_i18n_value(self.name_i18n, locale) or self.name_uk

    def get_description(self, locale: str = "uk") -> str:
        return get_i18n_value(self.description_i18n, locale) or self.description

    def __str__(self) -> str:
        return self.get_name("uk")