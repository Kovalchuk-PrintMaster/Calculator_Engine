# admin_app/catalog/models/model_materials.py
from django.db import models

class Material(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name_uk = models.CharField(max_length=255)

    class Meta:
        db_table = "materials"
        verbose_name = "Material"
        verbose_name_plural = "Materials"

    def __str__(self):
        return self.name_uk
