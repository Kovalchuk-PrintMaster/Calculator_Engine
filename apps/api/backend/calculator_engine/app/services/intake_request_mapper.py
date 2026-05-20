from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from calculator_engine.app.schemas.intake_v1 import ExternalQuoteIntakeRequestV1


class IntakeRequestMappingError(ValueError):
    """Raised when external intake request cannot be mapped."""


@dataclass(frozen=True, slots=True)
class IntakeRequestMappingResult:
    processing_payload: dict[str, Any]
    schema_version: str
    request_shape: str
    client_meta: dict[str, Any]


def _extract_validation_message(exc: ValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Invalid external intake request."

    first = errors[0]
    loc = ".".join(str(part) for part in first.get("loc", []))
    msg = first.get("msg", "Invalid value.")
    if loc:
        return f"Invalid external intake request field '{loc}': {msg}"
    return f"Invalid external intake request: {msg}"


def map_external_quote_intake_request(
    raw_payload: dict[str, Any],
) -> IntakeRequestMappingResult:
    """Map external intake payload into internal flat payload.

    Supports:
        - legacy flat payload
        - versioned envelope with schema_version='v1'
    """
    if not isinstance(raw_payload, dict):
        raise IntakeRequestMappingError("Intake payload must be a JSON object.")

    schema_version = raw_payload.get("schema_version")
    if schema_version is None:
        return IntakeRequestMappingResult(
            processing_payload=dict(raw_payload),
            schema_version="legacy-flat",
            request_shape="flat",
            client_meta={},
        )

    if schema_version != "v1":
        raise IntakeRequestMappingError(
            f"Unsupported intake schema_version: {schema_version}"
        )

    try:
        parsed = ExternalQuoteIntakeRequestV1.model_validate(raw_payload)
    except ValidationError as exc:
        raise IntakeRequestMappingError(_extract_validation_message(exc)) from exc

    processing_payload = parsed.data.model_dump(mode="python")
    existing_input_payload = processing_payload.get("input_payload_json") or {}

    processing_payload["input_payload_json"] = {
        **existing_input_payload,
        "_external_schema_version": parsed.schema_version,
        "_client": parsed.client.model_dump(mode="python"),
    }

    return IntakeRequestMappingResult(
        processing_payload=processing_payload,
        schema_version=parsed.schema_version,
        request_shape="external-envelope",
        client_meta=parsed.client.model_dump(mode="python"),
    )