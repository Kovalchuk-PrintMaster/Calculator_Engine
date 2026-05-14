from django.db import models


class MaterialOperationCapability(models.Model):
    material = models.ForeignKey(
        "catalog.Material",
        on_delete=models.CASCADE,
        related_name="operation_capabilities",
    )
    operation_type = models.ForeignKey(
        "catalog.OperationType",
        on_delete=models.CASCADE,
        related_name="material_capabilities",
    )

    is_allowed = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(default=100, db_index=True)
    constraints_json = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True, default="")
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "material_operation_capabilities"
        verbose_name = "Material operation capability"
        verbose_name_plural = "Material operation capabilities"
        ordering = ["material_id", "priority", "operation_type_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["material", "operation_type"],
                name="uq_material_operation_capability",
            )
        ]
        indexes = [
            models.Index(fields=["material", "active"]),
            models.Index(fields=["operation_type", "active"]),
        ]

    def __str__(self) -> str:
        return f"{self.material} -> {self.operation_type}"