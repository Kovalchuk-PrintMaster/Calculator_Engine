from __future__ import annotations

from decimal import Decimal

from django.db import models


class PriceUnit(models.TextChoices):
    ITEM = "item", "Item"
    SHEET = "sheet", "Sheet"
    ORDER = "order", "Order"


class MaterialPrice(models.Model):
    material = models.OneToOneField(
        "catalog.Material",
        on_delete=models.CASCADE,
        related_name="price",
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(
        max_length=16,
        choices=PriceUnit.choices,
        default=PriceUnit.SHEET,
        db_index=True,
    )
    waste_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "material_prices"
        verbose_name = "Material price"
        verbose_name_plural = "Material prices"
        ordering = ["material__name_uk"]

    def __str__(self) -> str:
        return f"{self.material} / {self.price} {self.unit}"


class OperationPrice(models.Model):
    operation_type = models.OneToOneField(
        "catalog.OperationType",
        on_delete=models.CASCADE,
        related_name="price",
    )
    setup_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    unit = models.CharField(
        max_length=16,
        choices=PriceUnit.choices,
        default=PriceUnit.ITEM,
        db_index=True,
    )
    active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "operation_prices"
        verbose_name = "Operation price"
        verbose_name_plural = "Operation prices"
        ordering = ["operation_type__group", "operation_type__sort_order", "operation_type__name_uk"]

    def __str__(self) -> str:
        return f"{self.operation_type} / {self.unit_price} {self.unit}"