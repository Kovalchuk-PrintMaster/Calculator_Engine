# python apps/admin/manage.py runserver 127.0.0.1:8001
"""
📄 Назва: catalog.admin (autoloader)
🧠 Призначення: імпортує всі модулі всередині пакета admin/*,
   щоби відпрацювали @admin.register(...) або admin.site.register(...).
"""

from __future__ import annotations

import importlib
import pkgutil

# __path__ вказує на теку цього пакета (admin/)
for _info in pkgutil.iter_modules(__path__, __name__ + "."):
    # Імпортуємо кожен admin_*.py, що лежить поряд
    importlib.import_module(_info.name)

del importlib, pkgutil, _info

from .admin_material_categories import *
from .admin_operation_types import *
from .admin_materials import *
from .admin_product_types import *
from .admin_product_templates import *
from .admin_capabilities import *
from .admin_pricing import *
from .admin_ui import *
from .admin_calculation_jobs import *
