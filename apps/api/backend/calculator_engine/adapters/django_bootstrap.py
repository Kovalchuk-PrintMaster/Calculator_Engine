"""Bootstrap Django ORM for FastAPI bridge access."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import django
from django.apps import apps as django_apps

_BOOTSTRAPPED = False


def setup_django() -> None:
    """Initialize Django once for catalog bridge access."""
    global _BOOTSTRAPPED

    if _BOOTSTRAPPED or django_apps.ready:
        _BOOTSTRAPPED = True
        return

    app_root = Path(__file__).resolve().parents[5]
    admin_root = app_root / "apps" / "admin"

    if str(admin_root) not in sys.path:
        sys.path.insert(0, str(admin_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calc_admin.settings")
    django.setup()
    _BOOTSTRAPPED = True