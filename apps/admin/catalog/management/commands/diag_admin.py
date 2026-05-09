from django.core.management.base import BaseCommand
from django.contrib import admin as dj
from django.apps import apps

class Command(BaseCommand):
    help = "Діагностика адмінки: які додатки/моделі підхоплені"

    def handle(self, *args, **opts):
        self.stdout.write("📦 INSTALLED APPS:")
        for a in apps.get_app_configs():
            self.stdout.write(f"  - {a.label} ({a.name})")

        dj.autodiscover()
        regs = sorted([m.__name__ for m in dj.site._registry])
        self.stdout.write("\n🧾 Зареєстровано в admin.site:")
        for r in regs:
            self.stdout.write(f"  - {r}")

        try:
            import catalog
            self.stdout.write(f"\n✅ catalog loaded from: {catalog.__file__}")
            import catalog.admin as cadmin
            self.stdout.write(f"✅ catalog.admin loaded from: {cadmin.__file__}")
            import catalog.models as cmodels
            upper = [x for x in dir(cmodels) if x[:1].isupper()]
            self.stdout.write(f"✅ catalog.models exported symbols: {upper}")
        except Exception as e:
            self.stderr.write(f"❌ Import error: {e}")
