# apps/admin/catalog/models/model_product_kinds.py
from django.db import models


class ProductKind(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name_uk = models.CharField(max_length=255)

    class Meta:
        db_table = "product_kinds"
        verbose_name = "Product kind"
        verbose_name_plural = "Product kinds"

    def __str__(self):
        return self.name_uk
