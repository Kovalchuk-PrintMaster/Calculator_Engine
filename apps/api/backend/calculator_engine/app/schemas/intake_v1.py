from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExternalClientMetaSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    channel: Literal["web", "mobile", "site", "api"] = "web"
    device: Literal["desktop", "mobile", "tablet", "unknown"] = "unknown"
    app_version: str | None = None
    platform: str | None = None


class ExternalQuoteIntakeDataV1(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: Literal["manual", "external"] = "external"

    brand_code: str = ""
    customer_ref: str = ""
    external_order_id: str | None = None
    external_customer_id: str | None = None
    idempotency_key: str | None = None

    product_template_code: str
    material_code: str
    quantity: int
    selected_operation_codes: list[str] = Field(default_factory=list)

    locale: str | None = None
    currency: str | None = None

    input_payload_json: dict = Field(default_factory=dict)


class ExternalQuoteIntakeRequestV1(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str
    client: ExternalClientMetaSchema = Field(default_factory=ExternalClientMetaSchema)
    data: ExternalQuoteIntakeDataV1