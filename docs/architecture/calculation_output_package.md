# Calculation Output Package

## Purpose

Calculator Engine is the formalization point between raw calculation input and downstream-ready structured output.

The purpose of the Calculation Output Package is to group calculator-owned outputs into one explicit machine-readable package.

## What Calculator owns here

Calculator owns:

- calculation logic
- calculation snapshots
- price breakdown
- material consumption estimate
- quote draft / commercial offer draft
- calculation report projections
- order draft / order creation draft structures
- calculation output package

## What Calculator does not own

Calculator does not own:

- canonical product/material catalog
- canonical client registry
- canonical order registry
- accounting truth
- warehouse truth
- CRM workflow ownership
- prepress lifecycle ownership
- Gateway runtime routing

## Quote draft vs order draft

### Quote draft
Quote draft is the commercial/calculator-facing summary of the calculation result.

It answers:

- what was priced
- for what quantity
- with which material
- with which route
- for which subtotal/total

### Order draft
Order draft is not a canonical order registry record.

It is only an order creation draft / formalized downstream-ready draft structure.

It helps later systems understand:

- what should be created downstream
- which product/material/quantity was calculated
- which estimated total should be propagated
- which downstream references may later be attached

## Local catalog projections

Current local catalog data may be used as:

- projection
- cache
- fixture
- sandbox data
- development helper

It is not canonical truth.

Canonical product/service/material/operation definitions are expected to belong to ForPrint Library in the future.

## How future modules may consume the package

Future consumers may include:

- Operational Registry
- Accounting
- Prepress

The package is designed to help those future consumers read structured calculator outputs without transferring ownership away from Calculator.

## Saved calculation job access

Calculation Output Package may be built from a saved Calculator job snapshot.

This gives Calculator a stable report-facing output for downstream-safe structured access.

Current intended access pattern:

- saved calculation job
- output package builder
- report-facing output package endpoint

This still does not create direct runtime integration with Operational Registry, Accounting, or Prepress.