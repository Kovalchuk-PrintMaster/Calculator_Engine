# Calculator Result Projections

## Purpose

Calculator Engine owns calculation result projections.

These are direct outputs of calculation execution and remain Calculator-owned even if later consumed by other modules.

## Calculator-owned result projections

The following result projections are Calculator-owned:

- calculation_execution_snapshot
- human_report
- external_report
- explicit_price_breakdown
- route_snapshot
- calculation_output_snapshot
- calculation_job_result_snapshot

## Meaning

These projections are calculation results.

They are not:

- operational order truth
- warehouse reservation truth
- accounting truth
- CRM workflow truth
- payment/invoice truth

## Downstream consumption

These projections may later be consumed by:

- CRM
- Operational Registry
- Gateway
- Website
- Telegram Bot
- Mobile App
- Accounting Registry
- Warehouse Service

Downstream consumption does not transfer ownership.

## Snapshot rule

CalculationJob stores a calculation result snapshot.

That snapshot is:

- immutable enough for reporting/reference
- calculation-oriented
- safe to expose through narrow report endpoints

It must not silently evolve into:

- order registry
- invoice registry
- warehouse document
- production workflow registry

## Explicit price breakdown

price_breakdown must remain explicit.

It must continue exposing:

- route
- line items
- subtotal
- total

material_consumption_estimate may complement price_breakdown, but must not replace it.

## Human and external reports

human_report and external_report are calculation report projections.

They are derived result views of the same calculation snapshot.

They are not separate operational systems.

## Direct external intake boundary

Current direct external intake is development-only and boundary-limited.

It is allowed for internal development and integration preparation.

It must not become:

- broad operational CRUD
- general backend
- Gateway replacement
- production integration authority

Future production intake should move through approved integration boundaries.