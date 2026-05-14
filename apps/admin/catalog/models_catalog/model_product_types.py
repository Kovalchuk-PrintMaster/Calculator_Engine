from django.db import models

from catalog.utils import get_i18n_value


class ProductType(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name_uk = models.CharField(max_length=255)
    name_i18n = models.JSONField(default=dict, blank=True)

    description = models.TextField(blank=True, default="")
    description_i18n = models.JSONField(default=dict, blank=True)

    active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=100, db_index=True)

    class Meta:
        db_table = "product_types"
        verbose_name = "Product type"
        verbose_name_plural = "Product types"
        ordering = ["sort_order", "name_uk"]

    def get_name(self, locale: str = "uk") -> str:
        return get_i18n_value(self.name_i18n, locale) or self.name_uk

    def get_description(self, locale: str = "uk") -> str:
        return get_i18n_value(self.description_i18n, locale) or self.description

    def __str__(self) -> str:
        return self.get_name("uk")


ProductKind = ProductType