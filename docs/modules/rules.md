# Правила/політики (масові зміни)

## Життєвий цикл
`draft → dry-run (DIFF) → approve → apply → rollback`

## Формат політики (JSON)
```json
{
  "selector": {"category": "Textiles", "attributes.color": {"$ne": "black"}},
  "operation": {"action": "percent_markup", "value": 7, "target": "tiers.unit_price"}
}
