from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Material, MaterialPrice, OperationPrice, OperationType


@dataclass(frozen=True, slots=True)
class OperationPriceSeed:
    code: str
    setup_price: Decimal
    unit_price: Decimal
    unit: str
    notes: str = ""


OPERATION_PRICES: tuple[OperationPriceSeed, ...] = (
    OperationPriceSeed("digital_print", Decimal("0.00"), Decimal("1.50"), "item"),
    OperationPriceSeed("uv_print", Decimal("80.00"), Decimal("2.20"), "item"),
    OperationPriceSeed("eco_solvent_print", Decimal("120.00"), Decimal("3.00"), "item"),
    OperationPriceSeed("guillotine_cut", Decimal("0.00"), Decimal("0.20"), "item"),
    OperationPriceSeed("contour_cut", Decimal("50.00"), Decimal("0.80"), "item"),
    OperationPriceSeed("lamination", Decimal("0.00"), Decimal("0.70"), "item"),
    OperationPriceSeed("foil", Decimal("150.00"), Decimal("1.50"), "item"),
    OperationPriceSeed("emboss", Decimal("120.00"), Decimal("1.20"), "item"),
    OperationPriceSeed("crease", Decimal("0.00"), Decimal("0.15"), "item"),
)


class Command(BaseCommand):
    help = "Seed demo pricing for operations and sample material."

    @transaction.atomic
    def handle(self, *args, **options):
        operation_counter = 0

        for item in OPERATION_PRICES:
            operation = OperationType.objects.get(code=item.code)
            OperationPrice.objects.update_or_create(
                operation_type=operation,
                defaults={
                    "setup_price": item.setup_price,
                    "unit_price": item.unit_price,
                    "unit": item.unit,
                    "active": True,
                    "notes": item.notes,
                },
            )
            operation_counter += 1

        material_counter = 0
        material = Material.objects.filter(code="tintoretto_neve_300").first()
        if material is not None:
            MaterialPrice.objects.update_or_create(
                material=material,
                defaults={
                    "price": Decimal("6.00"),
                    "unit": "sheet",
                    "waste_percent": Decimal("5.00"),
                    "active": True,
                    "notes": "Demo price for pricing foundation v1.",
                },
            )
            material_counter += 1
            self.stdout.write(
                self.style.SUCCESS("✅ Demo material price seeded for tintoretto_neve_300")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️ Material tintoretto_neve_300 not found, material price skipped")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Pricing demo seeded: operations={operation_counter}, materials={material_counter}"
            )
        )