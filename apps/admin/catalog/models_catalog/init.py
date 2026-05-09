# apps/admin/catalog/models/__init__.py
from .model_material_aliases import MaterialAlias
from .model_materials import Material
from .model_product_kinds import ProductKind
from .model_sizes import Size

__all__ = [
    "Size",
    "Material",
    "MaterialAlias",
    "ProductKind",
]
