from django.db import models


class ProductKindName(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name_uk = models.CharField(max_length=255)

    class Meta:
        db_table = "product_kind_names"
        verbose_name = "Product kind name"
        verbose_name_plural = "Product kind names"

    def __str__(self):
        return self.name_uk
