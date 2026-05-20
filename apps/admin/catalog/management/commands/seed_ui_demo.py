from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import ProductTemplate, UiBrand, UiBrandProductTemplateVisibility, UiSkin


SKINS = (
    {
        "code": "light_default",
        "name": "Light Default",
        "theme_json": {"mode": "light", "accent": "blue"},
        "sort_order": 10,
    },
    {
        "code": "light_poland",
        "name": "Light Poland",
        "theme_json": {"mode": "light", "accent": "red"},
        "sort_order": 20,
    },
)

BRANDS = (
    {
        "code": "printmaster_global",
        "name": "PrintMaster Global",
        "region_code": "GLOBAL",
        "default_locale": "en",
        "default_currency": "USD",
        "default_skin_code": "light_default",
        "sort_order": 10,
    },
    {
        "code": "printmaster_ua",
        "name": "PrintMaster Ukraine",
        "region_code": "UA",
        "default_locale": "uk",
        "default_currency": "EUR",
        "default_skin_code": "light_default",
        "sort_order": 20,
    },
    {
        "code": "printmaster_pl",
        "name": "PrintMaster Poland",
        "region_code": "PL",
        "default_locale": "pl",
        "default_currency": "EUR",
        "default_skin_code": "light_poland",
        "sort_order": 30,
    },
)

VISIBILITIES = (
    ("printmaster_global", "business_card_standard", True, True, 10),
    ("printmaster_global", "flyer_standard", True, True, 20),
    ("printmaster_global", "poster_standard", True, True, 30),
    ("printmaster_ua", "business_card_standard", True, True, 10),
    ("printmaster_ua", "flyer_standard", True, True, 20),
    ("printmaster_ua", "sticker_sheet_standard", True, True, 30),
    ("printmaster_pl", "business_card_standard", True, True, 10),
    ("printmaster_pl", "flyer_standard", True, True, 20),
)


class Command(BaseCommand):
    help = "Seed demo UI skins, brands, and brand template visibility."

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_skins()
        self._seed_brands()
        self._seed_visibilities()
        self.stdout.write(self.style.SUCCESS("✅ UI demo seeded"))

    def _seed_skins(self) -> None:
        for item in SKINS:
            UiSkin.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "theme_json": item["theme_json"],
                    "active": True,
                    "sort_order": item["sort_order"],
                },
            )

    def _seed_brands(self) -> None:
        for item in BRANDS:
            skin = UiSkin.objects.get(code=item["default_skin_code"])
            UiBrand.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "region_code": item["region_code"],
                    "default_locale": item["default_locale"],
                    "default_currency": item["default_currency"],
                    "default_skin": skin,
                    "settings_json": {},
                    "active": True,
                    "sort_order": item["sort_order"],
                },
            )

    def _seed_visibilities(self) -> None:
        for brand_code, template_code, is_visible, default_enabled, sort_order in VISIBILITIES:
            brand = UiBrand.objects.get(code=brand_code)
            template = ProductTemplate.objects.get(code=template_code)

            UiBrandProductTemplateVisibility.objects.update_or_create(
                brand=brand,
                product_template=template,
                defaults={
                    "is_visible": is_visible,
                    "default_enabled": default_enabled,
                    "active": True,
                    "sort_order": sort_order,
                },
            )