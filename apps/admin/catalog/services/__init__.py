from .availability import AvailableOperation, get_available_operations
from .pricing import PricingDataError, QuoteLine, QuoteResult, build_price_quote
from .projection import (
    MaterialOption,
    ProductConfigurationPreview,
    build_product_configuration_preview,
    get_material_options_for_template,
)
from .route_builder import (
    RouteStep,
    RouteValidationError,
    build_route,
    validate_selected_operation_codes,
)
from .brand_projection import BrandCatalogProjection, BrandTemplateOption, build_brand_catalog_projection
from .calculation_contracts import CalculationRequest, CalculationResult
from .calculation_processor import (
    CalculationProcessingError,
    create_calculation_job,
    finalize_calculation_job,
    process_calculation_request,
    run_calculation_request,
)
from .report_projection import build_external_quote_response, build_human_quote_report
from .brand_runtime import BrandRuntimeDefaults, resolve_brand_runtime_defaults
from .calculation_processor import CalculationIdempotencyConflictError
from .catalog_sync import run_catalog_sync
from .imposition_service import build_imposition_job

from .material_consumption import (
    build_material_consumption_estimate,
    material_consumption_estimate_to_dict,
)

__all__ = [
    "AvailableOperation",
    "MaterialOption",
    "PricingDataError",
    "ProductConfigurationPreview",
    "QuoteLine",
    "QuoteResult",
    "RouteStep",
    "RouteValidationError",
    "build_price_quote",
    "build_product_configuration_preview",
    "build_route",
    "get_available_operations",
    "get_material_options_for_template",
    "validate_selected_operation_codes",
    "BrandCatalogProjection",
    "BrandTemplateOption",
    "build_brand_catalog_projection",
    "CalculationProcessingError",
    "CalculationRequest",
    "CalculationResult",
    "build_external_quote_response",
    "build_human_quote_report",
    "create_calculation_job",
    "finalize_calculation_job",
    "process_calculation_request",
    "run_calculation_request",
    "BrandRuntimeDefaults",
    "resolve_brand_runtime_defaults",
    "CalculationIdempotencyConflictError",
]