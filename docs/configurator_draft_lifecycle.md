# Configurator Draft Lifecycle

## Lifecycle states

Calculator draft lifecycle may include:

- draft
- configuration_in_progress
- quote_ready
- submitted
- archived

## Meanings

### draft
No product template selected yet.

### configuration_in_progress
Template is selected, but draft is not yet fully ready for quote.

### quote_ready
Template, material, and quantity are present.
Draft is ready for quote preview, material consumption estimate, and submit.

### submitted
Draft has already been submitted and produced calculation outputs.

### archived
Optional later state for closed/inactive drafts.

## Boundary

This lifecycle belongs to Calculator only as quote/configurator lifecycle.

It is not canonical order lifecycle.

Operational Registry may later own canonical order lifecycle outside Calculator.