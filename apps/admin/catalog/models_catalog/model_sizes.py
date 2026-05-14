# apps/admin/catalog/models/model_sizes.py
from django.db import models


class Size(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    kind = models.ForeignKey(
        "catalog.ProductType",  # FK на сутність довідника видів
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sizes",
    )
    width_mm = models.PositiveIntegerField()
    height_mm = models.PositiveIntegerField()
    label_uk = models.CharField(max_length=255)
    label_ru = models.CharField(max_length=255, blank=True, default="")
    label_en = models.CharField(max_length=255, blank=True, default="")
    name_uk = models.CharField(max_length=255, blank=True, default="")
    name_ru = models.CharField(max_length=255, blank=True, default="")
    name_en = models.CharField(max_length=255, blank=True, default="")
    is_vertical = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sizes"
        verbose_name = "Size"
        verbose_name_plural = "Sizes"
        constraints = [models.UniqueConstraint(fields=("code",), name="uq_sizes_code")]

    def __str__(self):
        return f"{self.code} ({self.width_mm}×{self.height_mm} мм)"
