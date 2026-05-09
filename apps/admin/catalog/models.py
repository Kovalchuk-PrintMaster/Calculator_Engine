"""
Єдина точка входу для моделей каталогу.

Автоматично імпортує всі модулі з `models_catalog`
і експортує всі Django-моделі в namespace `catalog.models`.

Після цього в admin-модулях можна робити:
    from ..models import Size, ProductKind
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from django.db import models as django_models

from . import models_catalog as _models_catalog

__all__: list[str] = []


def _is_django_model(obj: object) -> bool:
    """Перевіряє, чи об'єкт є класом Django-моделі."""
    return (
        inspect.isclass(obj)
        and issubclass(obj, django_models.Model)
        and obj is not django_models.Model
    )


for _info in pkgutil.iter_modules(
    _models_catalog.__path__,
    _models_catalog.__name__ + ".",
):
    _module = importlib.import_module(_info.name)

    for _name, _value in vars(_module).items():
        if not _is_django_model(_value):
            continue

        if _name in globals() and globals()[_name] is not _value:
            raise RuntimeError(f"Duplicate model export detected in catalog.models: {_name}")

        globals()[_name] = _value
        __all__.append(_name)
