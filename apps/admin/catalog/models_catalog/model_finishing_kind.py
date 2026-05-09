# apps/admin/models_catalog/model_finishing_kind.py
from django.db import models

class FinishingKind(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name_uk = models.CharField(max_length=255)

    class Meta:
        db_table = "finishing_kind"
        verbose_name = "Finishing Kind"
        verbose_name_plural = "Finishing Kind"

    def __str__(self):
        return self.name_uk
