# Модель даних (огляд)

## Сутності (високий рівень)
- **products**(product_id, category, name, unit, is_active)
- **variants**(variant_id, product_id→products, attributes: JSONB, sku UNIQUE)
- **tiers**(variant_id→variants, qty_min, qty_max, unit_price, lead_time_days)
- **options**(option_id, name, type, calc, value, conditions: JSONB)
- **audience_pricing**(audience, modifier_type, value)
- **pricing_policies**(policy_id, selector: JSONB, operation: JSONB, status, created_by, created_at)
- **policy_runs**(run_id, policy_id→pricing_policies, dry_run, started_at, finished_at, status, affected_rows, error)
- **change_log**(id, run_id→policy_runs, table_name, pk: JSONB, column, old_value, new_value, changed_at, changed_by)
- **config_snapshots**(config_id, product_id, attributes: JSONB, qty, audience, price_breakdown: JSONB, created_at)
- **assets**(id, product_id, kind, url)

## Поради по індексації
- GIN-індекси на шляхах JSONB, які часто фільтруються (напр., attributes->>'color').
- Складений PK для tiers: `(variant_id, qty_min)`.
- Partial indexes для `is_active = true`.
- Матеріалізовані в’юхи для “from-price” у каталозі.

## Підхід до JSONB
- Гібридна схема: гарячі/часті атрибути — типізовані колонки; рідкісні — JSONB.
- Можливе використання generated columns для швидких фільтрів.
