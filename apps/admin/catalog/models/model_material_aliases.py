# admin_app/catalog/models/model_material_aliases.py
from django.db import models

class MaterialAlias(models.Model):
    material = models.ForeignKey("catalog.Material", on_delete=models.CASCADE, related_name="aliases")
    alias = models.CharField(max_length=255, db_index=True)

    class Meta:
        db_table = "material_aliases"
        verbose_name = "Material alias"
        verbose_name_plural = "Material aliases"
        unique_together = [("material", "alias")]

    def __str__(self):
        return f"{self.material} → {self.alias}"
