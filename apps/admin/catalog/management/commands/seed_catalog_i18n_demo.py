from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Material, MaterialCategory, OperationType, ProductTemplate, ProductType


PRODUCT_TYPE_I18N = {
    "business_card": {
        "name_i18n": {
            "uk": "Візитка",
            "en": "Business Card",
            "pl": "Wizytówka",
            "de": "Visitenkarte",
        },
        "description_i18n": {
            "uk": "Базовий тип для візиток.",
            "en": "Base type for business cards.",
            "pl": "Bazowy typ dla wizytówek.",
            "de": "Basistyp für Visitenkarten.",
        },
    },
    "flyer": {
        "name_i18n": {
            "uk": "Флаєр",
            "en": "Flyer",
            "pl": "Ulotka",
            "de": "Flyer",
        },
        "description_i18n": {
            "uk": "Листовий рекламний виріб.",
            "en": "Leaf advertising product.",
            "pl": "Arkuszowy produkt reklamowy.",
            "de": "Werbeprodukt im Bogenformat.",
        },
    },
    "poster": {
        "name_i18n": {
            "uk": "Постер",
            "en": "Poster",
            "pl": "Plakat",
            "de": "Poster",
        },
        "description_i18n": {
            "uk": "Плакат або афіша.",
            "en": "Poster or billboard print.",
            "pl": "Plakat lub afisz.",
            "de": "Poster oder Aushang.",
        },
    },
    "sticker": {
        "name_i18n": {
            "uk": "Наклейка",
            "en": "Sticker",
            "pl": "Naklejka",
            "de": "Aufkleber",
        },
        "description_i18n": {
            "uk": "Самоклейний виріб.",
            "en": "Self-adhesive product.",
            "pl": "Produkt samoprzylepny.",
            "de": "Selbstklebendes Produkt.",
        },
    },
}

MATERIAL_CATEGORY_I18N = {
    "sheet_paper": {
        "name_i18n": {
            "uk": "Листовий папір",
            "en": "Sheet Paper",
            "pl": "Papier arkuszowy",
            "de": "Bogenpapier",
        },
        "description_i18n": {
            "uk": "Базові листові папери для друку.",
            "en": "Basic sheet papers for printing.",
            "pl": "Podstawowe papiery arkuszowe do druku.",
            "de": "Grundlegende Bogenpapiere zum Drucken.",
        },
    },
    "designer_cardstock": {
        "name_i18n": {
            "uk": "Дизайнерський картон",
            "en": "Designer Cardstock",
            "pl": "Karton ozdobny",
            "de": "Designer-Karton",
        },
        "description_i18n": {
            "uk": "Преміальні дизайнерські картони.",
            "en": "Premium designer cardstocks.",
            "pl": "Premium kartony ozdobne.",
            "de": "Premium-Designer-Kartons.",
        },
    },
    "self_adhesive_paper": {
        "name_i18n": {
            "uk": "Самоклейний папір",
            "en": "Self-Adhesive Paper",
            "pl": "Papier samoprzylepny",
            "de": "Selbstklebendes Papier",
        },
        "description_i18n": {
            "uk": "Самоклейні паперові матеріали.",
            "en": "Self-adhesive paper materials.",
            "pl": "Samoprzylepne materiały papierowe.",
            "de": "Selbstklebende Papiermaterialien.",
        },
    },
    "self_adhesive_film": {
        "name_i18n": {
            "uk": "Самоклейна плівка",
            "en": "Self-Adhesive Film",
            "pl": "Folia samoprzylepna",
            "de": "Selbstklebefolie",
        },
        "description_i18n": {
            "uk": "Самоклейні плівки для друку та порізки.",
            "en": "Self-adhesive films for printing and cutting.",
            "pl": "Folie samoprzylepne do druku i cięcia.",
            "de": "Selbstklebefolien für Druck und Zuschnitt.",
        },
    },
    "banner": {
        "name_i18n": {
            "uk": "Банер",
            "en": "Banner",
            "pl": "Baner",
            "de": "Banner",
        },
        "description_i18n": {
            "uk": "Рулонні банерні матеріали.",
            "en": "Roll banner materials.",
            "pl": "Materiały banerowe w rolkach.",
            "de": "Banner-Materialien auf Rollen.",
        },
    },
}

OPERATION_TYPE_I18N = {
    "digital_print": {
        "name_i18n": {
            "uk": "Цифровий друк",
            "en": "Digital Print",
            "pl": "Druk cyfrowy",
            "de": "Digitaldruck",
        },
        "description_i18n": {
            "uk": "Базовий цифровий друк на листових матеріалах.",
            "en": "Basic digital printing on sheet materials.",
            "pl": "Podstawowy druk cyfrowy na materiałach arkuszowych.",
            "de": "Grundlegender Digitaldruck auf Bogenmaterialien.",
        },
    },
    "uv_print": {
        "name_i18n": {
            "uk": "UV-друк",
            "en": "UV Print",
            "pl": "Druk UV",
            "de": "UV-Druck",
        },
        "description_i18n": {
            "uk": "УФ-друк на твердих та спеціальних матеріалах.",
            "en": "UV printing on rigid and specialty materials.",
            "pl": "Druk UV na materiałach sztywnych i specjalnych.",
            "de": "UV-Druck auf starren und Spezialmaterialien.",
        },
    },
    "eco_solvent_print": {
        "name_i18n": {
            "uk": "Екосольвентний друк",
            "en": "Eco-Solvent Print",
            "pl": "Druk ekosolwentowy",
            "de": "Eco-Solvent-Druck",
        },
        "description_i18n": {
            "uk": "Широкоформатний друк по рулонних матеріалах.",
            "en": "Wide-format printing on roll materials.",
            "pl": "Druk wielkoformatowy na materiałach rolowych.",
            "de": "Großformatdruck auf Rollenmaterialien.",
        },
    },
    "guillotine_cut": {
        "name_i18n": {
            "uk": "Гільйотинна порізка",
            "en": "Guillotine Cut",
            "pl": "Cięcie gilotynowe",
            "de": "Guillotineschnitt",
        },
        "description_i18n": {
            "uk": "Пряма листова порізка.",
            "en": "Straight sheet cutting.",
            "pl": "Proste cięcie arkuszy.",
            "de": "Gerader Bogenschnitt.",
        },
    },
    "contour_cut": {
        "name_i18n": {
            "uk": "Фігурна порізка",
            "en": "Contour Cut",
            "pl": "Cięcie konturowe",
            "de": "Konturschnitt",
        },
        "description_i18n": {
            "uk": "Контурна/фігурна порізка.",
            "en": "Contour or shape cutting.",
            "pl": "Cięcie konturowe lub kształtowe.",
            "de": "Kontur- oder Formschnitt.",
        },
    },
    "lamination": {
        "name_i18n": {
            "uk": "Ламінація",
            "en": "Lamination",
            "pl": "Laminacja",
            "de": "Laminierung",
        },
        "description_i18n": {
            "uk": "Глянцева або матова ламінація.",
            "en": "Gloss or matte lamination.",
            "pl": "Laminacja błyszcząca lub matowa.",
            "de": "Glanz- oder Mattlaminierung.",
        },
    },
    "foil": {
        "name_i18n": {
            "uk": "Фольгування",
            "en": "Foil Stamping",
            "pl": "Złocenie folią",
            "de": "Folienprägung",
        },
        "description_i18n": {
            "uk": "Нанесення фольги на матеріал.",
            "en": "Applying foil to material.",
            "pl": "Nakładanie folii na materiał.",
            "de": "Aufbringen von Folie auf das Material.",
        },
    },
    "emboss": {
        "name_i18n": {
            "uk": "Тиснення",
            "en": "Embossing",
            "pl": "Tłoczenie",
            "de": "Prägung",
        },
        "description_i18n": {
            "uk": "Конгревне або блинтове тиснення.",
            "en": "Raised or blind embossing.",
            "pl": "Tłoczenie wypukłe lub ślepe.",
            "de": "Relief- oder Blindprägung.",
        },
    },
    "crease": {
        "name_i18n": {
            "uk": "Біговка",
            "en": "Creasing",
            "pl": "Bigowanie",
            "de": "Rillen",
        },
        "description_i18n": {
            "uk": "Підготовка до згину.",
            "en": "Preparation for folding.",
            "pl": "Przygotowanie do składania.",
            "de": "Vorbereitung zum Falzen.",
        },
    },
}

PRODUCT_TEMPLATE_I18N = {
    "business_card_standard": {
        "name_i18n": {
            "uk": "Візитка стандарт",
            "en": "Business Card Standard",
            "pl": "Wizytówka standard",
            "de": "Visitenkarte Standard",
        },
        "description_i18n": {
            "uk": "Базова конфігурація візитки.",
            "en": "Basic business card configuration.",
            "pl": "Podstawowa konfiguracja wizytówki.",
            "de": "Grundkonfiguration der Visitenkarte.",
        },
    },
    "flyer_standard": {
        "name_i18n": {
            "uk": "Флаєр стандарт",
            "en": "Flyer Standard",
            "pl": "Ulotka standard",
            "de": "Flyer Standard",
        },
        "description_i18n": {
            "uk": "Базова конфігурація флаєра.",
            "en": "Basic flyer configuration.",
            "pl": "Podstawowa konfiguracja ulotki.",
            "de": "Grundkonfiguration des Flyers.",
        },
    },
    "poster_standard": {
        "name_i18n": {
            "uk": "Постер стандарт",
            "en": "Poster Standard",
            "pl": "Plakat standard",
            "de": "Poster Standard",
        },
        "description_i18n": {
            "uk": "Базова конфігурація постера.",
            "en": "Basic poster configuration.",
            "pl": "Podstawowa konfiguracja plakatu.",
            "de": "Grundkonfiguration des Posters.",
        },
    },
    "sticker_sheet_standard": {
        "name_i18n": {
            "uk": "Наклейка листова стандарт",
            "en": "Sheet Sticker Standard",
            "pl": "Naklejka arkuszowa standard",
            "de": "Bogenaufkleber Standard",
        },
        "description_i18n": {
            "uk": "Базова конфігурація наклейки.",
            "en": "Basic sticker configuration.",
            "pl": "Podstawowa konfiguracja naklejki.",
            "de": "Grundkonfiguration des Aufklebers.",
        },
    },
}

MATERIAL_I18N = {
    "tintoretto_neve_300": {
        "name_i18n": {
            "uk": "Tintoretto Neve 300",
            "en": "Tintoretto Neve 300",
            "pl": "Tintoretto Neve 300",
            "de": "Tintoretto Neve 300",
        },
    },
}


class Command(BaseCommand):
    help = "Seed demo i18n translations for catalog foundation entities."

    @transaction.atomic
    def handle(self, *args, **options):
        updated = 0

        updated += self._apply(ProductType, PRODUCT_TYPE_I18N)
        updated += self._apply(MaterialCategory, MATERIAL_CATEGORY_I18N)
        updated += self._apply(OperationType, OPERATION_TYPE_I18N)
        updated += self._apply(ProductTemplate, PRODUCT_TEMPLATE_I18N)
        updated += self._apply(Material, MATERIAL_I18N)

        self.stdout.write(self.style.SUCCESS(f"✅ Catalog i18n demo seeded: {updated} updated"))

    def _apply(self, model, data: dict[str, dict]) -> int:
        counter = 0
        for code, payload in data.items():
            obj = model.objects.filter(code=code).first()
            if obj is None:
                continue

            for field_name, field_value in payload.items():
                setattr(obj, field_name, field_value)

            obj.save(update_fields=list(payload.keys()))
            counter += 1
        return counter