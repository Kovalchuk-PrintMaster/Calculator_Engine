from __future__ import annotations

from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import (
    MaterialCategory,
    OperationType,
    ProductTemplate,
    ProductTemplateOperation,
    ProductType,
)
from catalog.utils import make_i18n_value


@dataclass(frozen=True, slots=True)
class CategorySeed:
    code: str
    name_uk: str
    description: str
    form_factor: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class OperationSeed:
    code: str
    name_uk: str
    group: str
    handler_code: str
    description: str
    requires_setup: bool
    sort_order: int


@dataclass(frozen=True, slots=True)
class ProductTypeSeed:
    code: str
    name_uk: str
    description: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class TemplateOperationSeed:
    operation_code: str
    is_required: bool
    is_optional: bool
    default_enabled: bool
    sequence_order: int


@dataclass(frozen=True, slots=True)
class ProductTemplateSeed:
    code: str
    name_uk: str
    product_type_code: str
    description: str
    sort_order: int
    allowed_material_categories_json: list[str]
    parameter_schema_json: dict
    ui_schema_json: dict
    route_profile: str
    pricing_profile: str
    operations: tuple[TemplateOperationSeed, ...]


CATEGORIES: tuple[CategorySeed, ...] = (
    CategorySeed(
        code="sheet_paper",
        name_uk="Листовий папір",
        description="Базові листові папери для друку.",
        form_factor="sheet",
        sort_order=10,
    ),
    CategorySeed(
        code="designer_cardstock",
        name_uk="Дизайнерський картон",
        description="Преміальні дизайнерські картони.",
        form_factor="sheet",
        sort_order=20,
    ),
    CategorySeed(
        code="self_adhesive_paper",
        name_uk="Самоклейний папір",
        description="Самоклейні паперові матеріали.",
        form_factor="sheet",
        sort_order=30,
    ),
    CategorySeed(
        code="self_adhesive_film",
        name_uk="Самоклейна плівка",
        description="Самоклейні плівки для друку та порізки.",
        form_factor="roll",
        sort_order=40,
    ),
    CategorySeed(
        code="banner",
        name_uk="Банер",
        description="Рулонні банерні матеріали.",
        form_factor="roll",
        sort_order=50,
    ),
)

OPERATIONS: tuple[OperationSeed, ...] = (
    OperationSeed(
        code="digital_print",
        name_uk="Цифровий друк",
        group="print",
        handler_code="digital_print",
        description="Базовий цифровий друк на листових матеріалах.",
        requires_setup=False,
        sort_order=10,
    ),
    OperationSeed(
        code="uv_print",
        name_uk="UV-друк",
        group="print",
        handler_code="uv_print",
        description="УФ-друк на твердих та спеціальних матеріалах.",
        requires_setup=True,
        sort_order=20,
    ),
    OperationSeed(
        code="eco_solvent_print",
        name_uk="Екосольвентний друк",
        group="print",
        handler_code="eco_solvent_print",
        description="Широкоформатний друк по рулонних матеріалах.",
        requires_setup=True,
        sort_order=30,
    ),
    OperationSeed(
        code="guillotine_cut",
        name_uk="Гільйотинна порізка",
        group="cutting",
        handler_code="guillotine_cut",
        description="Пряма листова порізка.",
        requires_setup=False,
        sort_order=40,
    ),
    OperationSeed(
        code="contour_cut",
        name_uk="Фігурна порізка",
        group="cutting",
        handler_code="contour_cut",
        description="Контурна/фігурна порізка.",
        requires_setup=True,
        sort_order=50,
    ),
    OperationSeed(
        code="lamination",
        name_uk="Ламінація",
        group="finishing",
        handler_code="lamination",
        description="Глянцева або матова ламінація.",
        requires_setup=False,
        sort_order=60,
    ),
    OperationSeed(
        code="foil",
        name_uk="Фольгування",
        group="finishing",
        handler_code="foil",
        description="Нанесення фольги на матеріал.",
        requires_setup=True,
        sort_order=70,
    ),
    OperationSeed(
        code="emboss",
        name_uk="Тиснення",
        group="finishing",
        handler_code="emboss",
        description="Конгревне або блинтове тиснення.",
        requires_setup=True,
        sort_order=80,
    ),
    OperationSeed(
        code="crease",
        name_uk="Біговка",
        group="finishing",
        handler_code="crease",
        description="Підготовка до згину.",
        requires_setup=False,
        sort_order=90,
    ),
)

PRODUCT_TYPES: tuple[ProductTypeSeed, ...] = (
    ProductTypeSeed(
        code="business_card",
        name_uk="Візитка",
        description="Базовий тип для візиток.",
        sort_order=10,
    ),
    ProductTypeSeed(
        code="flyer",
        name_uk="Флаєр",
        description="Листовий рекламний виріб.",
        sort_order=20,
    ),
    ProductTypeSeed(
        code="poster",
        name_uk="Постер",
        description="Плакат або афіша.",
        sort_order=30,
    ),
    ProductTypeSeed(
        code="sticker",
        name_uk="Наклейка",
        description="Самоклейний виріб.",
        sort_order=40,
    ),
)

PRODUCT_TEMPLATES: tuple[ProductTemplateSeed, ...] = (
    ProductTemplateSeed(
        code="business_card_standard",
        name_uk="Візитка стандарт",
        product_type_code="business_card",
        description="Базова конфігурація візитки.",
        sort_order=10,
        allowed_material_categories_json=["sheet_paper", "designer_cardstock"],
        parameter_schema_json={
            "quantity": {"type": "integer", "min": 1},
            "print_mode": {"type": "string"},
        },
        ui_schema_json={"group": "cards"},
        route_profile="flat_sheet_print",
        pricing_profile="flat_sheet_simple",
        operations=(
            TemplateOperationSeed("guillotine_cut", True, False, True, 10),
            TemplateOperationSeed("digital_print", False, True, True, 20),
            TemplateOperationSeed("uv_print", False, True, False, 30),
            TemplateOperationSeed("lamination", False, True, False, 40),
            TemplateOperationSeed("foil", False, True, False, 50),
            TemplateOperationSeed("emboss", False, True, False, 60),
        ),
    ),
    ProductTemplateSeed(
        code="flyer_standard",
        name_uk="Флаєр стандарт",
        product_type_code="flyer",
        description="Базова конфігурація флаєра.",
        sort_order=20,
        allowed_material_categories_json=["sheet_paper"],
        parameter_schema_json={
            "quantity": {"type": "integer", "min": 1},
            "print_mode": {"type": "string"},
        },
        ui_schema_json={"group": "leaflets"},
        route_profile="flat_sheet_print",
        pricing_profile="flat_sheet_simple",
        operations=(
            TemplateOperationSeed("guillotine_cut", True, False, True, 10),
            TemplateOperationSeed("digital_print", False, True, True, 20),
            TemplateOperationSeed("uv_print", False, True, False, 30),
            TemplateOperationSeed("lamination", False, True, False, 40),
        ),
    ),
    ProductTemplateSeed(
        code="poster_standard",
        name_uk="Постер стандарт",
        product_type_code="poster",
        description="Базова конфігурація постера.",
        sort_order=30,
        allowed_material_categories_json=["sheet_paper", "banner", "self_adhesive_film"],
        parameter_schema_json={
            "quantity": {"type": "integer", "min": 1},
            "print_mode": {"type": "string"},
        },
        ui_schema_json={"group": "wide_format"},
        route_profile="poster_print",
        pricing_profile="poster_simple",
        operations=(
            TemplateOperationSeed("guillotine_cut", True, False, True, 10),
            TemplateOperationSeed("digital_print", False, True, False, 20),
            TemplateOperationSeed("uv_print", False, True, False, 30),
            TemplateOperationSeed("eco_solvent_print", False, True, True, 40),
            TemplateOperationSeed("lamination", False, True, False, 50),
        ),
    ),
    ProductTemplateSeed(
        code="sticker_sheet_standard",
        name_uk="Наклейка листова стандарт",
        product_type_code="sticker",
        description="Базова конфігурація наклейки.",
        sort_order=40,
        allowed_material_categories_json=["self_adhesive_paper", "self_adhesive_film"],
        parameter_schema_json={
            "quantity": {"type": "integer", "min": 1},
            "print_mode": {"type": "string"},
        },
        ui_schema_json={"group": "stickers"},
        route_profile="sticker_sheet",
        pricing_profile="sticker_simple",
        operations=(
            TemplateOperationSeed("contour_cut", True, False, True, 10),
            TemplateOperationSeed("digital_print", False, True, True, 20),
            TemplateOperationSeed("uv_print", False, True, False, 30),
            TemplateOperationSeed("lamination", False, True, False, 40),
        ),
    ),
)


class Command(BaseCommand):
    help = "Seed base catalog foundation: categories, operation types, product types, templates."

    @transaction.atomic
    def handle(self, *args, **options):
        created_categories = self._seed_categories()
        created_operations = self._seed_operations()
        created_product_types = self._seed_product_types()
        created_templates, created_template_operations = self._seed_product_templates()

        self.stdout.write(self.style.SUCCESS("✅ Catalog foundation seeded"))
        self.stdout.write(
            f"   Categories: {created_categories} created/updated\n"
            f"   Operations: {created_operations} created/updated\n"
            f"   Product types: {created_product_types} created/updated\n"
            f"   Templates: {created_templates} created/updated\n"
            f"   Template operations: {created_template_operations} created/updated"
        )

    def _seed_categories(self) -> int:
        counter = 0
        for item in CATEGORIES:
            MaterialCategory.objects.update_or_create(
                code=item.code,
                defaults={
                    "name_uk": item.name_uk,
                    "name_i18n": make_i18n_value("uk", item.name_uk),
                    "description": item.description,
                    "description_i18n": make_i18n_value("uk", item.description),
                    "form_factor": item.form_factor,
                    "active": True,
                    "sort_order": item.sort_order,
                },
            )
            counter += 1
        return counter

    def _seed_operations(self) -> int:
        counter = 0
        for item in OPERATIONS:
            OperationType.objects.update_or_create(
                code=item.code,
                defaults={
                    "name_uk": item.name_uk,
                    "name_i18n": make_i18n_value("uk", item.name_uk),
                    "group": item.group,
                    "handler_code": item.handler_code,
                    "description": item.description,
                    "description_i18n": make_i18n_value("uk", item.description),
                    "requires_setup": item.requires_setup,
                    "active": True,
                    "sort_order": item.sort_order,
                },
            )
            counter += 1
        return counter

    def _seed_product_types(self) -> int:
        counter = 0
        for item in PRODUCT_TYPES:
            ProductType.objects.update_or_create(
                code=item.code,
                defaults={
                    "name_uk": item.name_uk,
                    "name_i18n": make_i18n_value("uk", item.name_uk),
                    "description": item.description,
                    "description_i18n": make_i18n_value("uk", item.description),
                    "active": True,
                    "sort_order": item.sort_order,
                },
            )
            counter += 1
        return counter

    def _seed_product_templates(self) -> tuple[int, int]:
        template_counter = 0
        template_operation_counter = 0

        operations_by_code = {
            item.code: item
            for item in OperationType.objects.filter(active=True)
        }
        product_types_by_code = {
            item.code: item
            for item in ProductType.objects.filter(active=True)
        }

        for item in PRODUCT_TEMPLATES:
            product_type = product_types_by_code[item.product_type_code]

            template, _ = ProductTemplate.objects.update_or_create(
                code=item.code,
                defaults={
                    "name_uk": item.name_uk,
                    "name_i18n": make_i18n_value("uk", item.name_uk),
                    "product_type": product_type,
                    "description": item.description,
                    "description_i18n": make_i18n_value("uk", item.description),
                    "active": True,
                    "sort_order": item.sort_order,
                    "allowed_material_categories_json": item.allowed_material_categories_json,
                    "parameter_schema_json": item.parameter_schema_json,
                    "ui_schema_json": item.ui_schema_json,
                    "route_profile": item.route_profile,
                    "pricing_profile": item.pricing_profile,
                },
            )
            template_counter += 1

            operation_codes: list[str] = []
            for op_item in item.operations:
                operation = operations_by_code[op_item.operation_code]
                operation_codes.append(op_item.operation_code)

                ProductTemplateOperation.objects.update_or_create(
                    product_template=template,
                    operation_type=operation,
                    defaults={
                        "is_required": op_item.is_required,
                        "is_optional": op_item.is_optional,
                        "default_enabled": op_item.default_enabled,
                        "sequence_order": op_item.sequence_order,
                        "constraints_json": {},
                        "active": True,
                    },
                )
                template_operation_counter += 1

            ProductTemplateOperation.objects.filter(
                product_template=template
            ).exclude(
                operation_type__code__in=operation_codes
            ).update(active=False)

        return template_counter, template_operation_counter