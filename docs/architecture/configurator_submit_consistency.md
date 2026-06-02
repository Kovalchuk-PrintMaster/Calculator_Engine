# Configurator Submit Consistency

## Purpose

Configurator submit must remain consistent with calculator quote preview.

## Required consistency

For a ready draft, the following calculator outputs must match between preview and submit result:

- currency
- subtotal
- total
- material_code
- quantity
- selected_operation_codes
- route codes

## Saved report consistency

Saved calculation job report must remain consistent with submit result for:

- total
- human_report material/code/route
- external_report material/code/route

## Boundary

This consistency policy belongs to Calculator Engine only as calculation flow hardening.

It does not create:

- order lifecycle ownership
- CRM workflow ownership
- Gateway authority
- accounting truth
- warehouse truth