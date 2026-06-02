# Calculation Scenario Coverage

## Purpose

Calculator Engine uses local scenario coverage to harden calculation behavior before full Library-driven catalog import becomes the default calculation source.

## Current rule

Temporary local catalog inputs are allowed for:

- quote preview hardening
- submit/report consistency hardening
- route behavior validation
- optional operation pricing validation
- material consumption estimate validation

These inputs remain:

- non-canonical
- local calculation inputs
- scenario fixtures
- development support data

## Scenario matrix policy

Scenario coverage should validate:

- route shape
- total stability
- optional operation effect
- quantity scaling effect
- material consumption estimate consistency
- preview/submit/report parity

## Boundary

Scenario coverage belongs to Calculator Engine as logic-first hardening.

It does not make Calculator the canonical owner of:

- product catalog
- material catalog
- order truth
- CRM truth
- warehouse truth