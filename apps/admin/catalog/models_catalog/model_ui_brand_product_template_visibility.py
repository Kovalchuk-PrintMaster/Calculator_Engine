from django.db import models


class UiBrandProductTemplateVisibility(models.Model):
    brand = models.ForeignKey(
        "catalog.UiBrand",
        on_delete=models.CASCADE,
        related_name="template_visibilities",
    )
    product_template = models.ForeignKey(
        "catalog.ProductTemplate",
        on_delete=models.CASCADE,
        related_name="brand_visibilities",
    )

    is_visible = models.BooleanField(default=True, db_index=True)
    default_enabled = models.BooleanField(default=True, db_index=True)
    active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=100, db_index=True)

    class Meta:
        db_table = "ui_brand_product_template_visibilities"
        verbose_name = "UI brand product template visibility"
        verbose_name_plural = "UI brand product template visibilities"
        ordering = ["brand_id", "sort_order", "product_template_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["brand", "product_template"],
                name="uq_ui_brand_product_template_visibility",
            )
        ]
        indexes = [
            models.Index(fields=["brand", "active"]),
            models.Index(fields=["product_template", "active"]),
        ]

    def __str__(self) -> str:
        return f"{self.brand} -> {self.product_template}"