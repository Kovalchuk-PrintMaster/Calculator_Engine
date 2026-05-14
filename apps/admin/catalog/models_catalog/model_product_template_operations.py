from django.db import models


class ProductTemplateOperation(models.Model):
    product_template = models.ForeignKey(
        "catalog.ProductTemplate",
        on_delete=models.CASCADE,
        related_name="template_operations",
    )
    operation_type = models.ForeignKey(
        "catalog.OperationType",
        on_delete=models.CASCADE,
        related_name="template_operations",
    )

    is_required = models.BooleanField(default=False, db_index=True)
    is_optional = models.BooleanField(default=True, db_index=True)
    default_enabled = models.BooleanField(default=False)
    sequence_order = models.PositiveIntegerField(default=100, db_index=True)

    constraints_json = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "product_template_operations"
        verbose_name = "Product template operation"
        verbose_name_plural = "Product template operations"
        ordering = ["product_template_id", "sequence_order", "operation_type_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product_template", "operation_type"],
                name="uq_product_template_operation",
            )
        ]
        indexes = [
            models.Index(fields=["product_template", "active"]),
            models.Index(fields=["operation_type", "active"]),
        ]

    def __str__(self) -> str:
        return f"{self.product_template} -> {self.operation_type}"