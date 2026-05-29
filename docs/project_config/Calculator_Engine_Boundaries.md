# Calculator Engine Boundaries

## Ownership

Calculator Engine owns:

- quote_draft
- price_breakdown
- product_configuration
- material_consumption_estimate
- calculation execution snapshots
- calculation-specific pricing rules
- calculation report projections

## Calculator result projections

Calculator-owned result projections include:

- calculation_execution_snapshot
- human_report
- external_report
- explicit_price_breakdown
- route_snapshot
- calculation_output_snapshot
- calculation_job_result_snapshot

These are Calculator outputs and may later be consumed by other modules.

## Non-canonical local catalog structures

The following local structures are not canonical truth:

- MaterialCategory
- Material
- OperationType
- ProductType
- ProductTemplate
- UiBrand
- UiSkin
- template visibility metadata
- imported catalog structures

Allowed meaning:

- imported calculation input
- local projection
- cache
- snapshot for fast calculation

Forbidden meaning:

- canonical product/material/catalog truth
- global brand/channel registry
- Library replacement

## Customer and order context

Calculator may receive:

- customer_ref
- external_customer_id
- order_ref
- source_channel
- request_context

These fields are:

- snapshot
- reference
- request context

Calculator does not own:

- client registry
- order registry
- CRM workflow
- operational history truth

## Technical handoff helpers

Trusted handoff helpers are allowed only as technical bridge/reference structures.

Examples:

- trusted_handoff_context
- handoff_reference
- request_bridge_context
- customer_identity_link_snapshot
- external_customer_ref
- source_channel_ref
- request_context_snapshot

These are not:

- CRM identity ownership
- auth system
- authorization system
- session management
- Gateway security ownership

## Material consumption estimate

material_consumption_estimate is Calculator-owned as an estimate only.

It is not:

- warehouse reservation
- stock truth
- stock writeoff
- accounting truth
- production issue record

Supported contexts:

- draft
- quote
- calculation_job
- standalone

## Imposition boundary

ImpositionJob is a technical shell only.

Calculator may keep:

- technical job shell
- layout/imposition estimation context
- future prepress handoff preparation

Calculator does not own:

- uploaded file lifecycle
- prepress file processing
- output file storage
- real prepress plugin execution

## External intake boundary

Current direct external intake is development-only and narrow.

It must not become:

- broad operational CRUD
- general backend
- Gateway replacement
- production integration authority

Future production flow should move through approved integration boundaries.

## Projection safeguard policy

Calculator must treat local catalog entities as non-canonical projections.

Runtime and test safeguards must enforce that these entities are used only as:

- calculation_input
- projection_cache
- snapshot

They must never be treated as:

- canonical_truth
- global_registry
- library_replacement

This applies especially to Library-sourced records and imported catalog projections.