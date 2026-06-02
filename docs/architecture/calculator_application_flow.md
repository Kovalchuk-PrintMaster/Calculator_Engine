# Calculator Application Flow

## Purpose

Calculator Engine provides calculator-facing application flow for:

- configurator draft creation
- configurator draft update
- configurator draft context
- quote preview
- material consumption estimate
- draft submit
- saved calculation report access

## Flow stages

1. draft creation
2. draft configuration
3. quote preview readiness
4. material consumption estimate readiness
5. submit
6. calculation result projection access

## Ownership

This is Calculator-owned application flow.

It is not:

- CRM workflow
- canonical order lifecycle
- Gateway routing/security
- warehouse reservation flow
- accounting workflow

## Temporary local catalog rule

Temporary local catalog inputs are allowed for logic hardening.

They remain:

- non-canonical
- calculation-facing
- scenario inputs
- local projection/cache/sandbox data