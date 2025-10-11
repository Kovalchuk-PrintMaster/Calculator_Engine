# База даних: схема та конвенції

## Рівні моделі
- **Каталог**: `products`, `variants`, `attributes (JSONB)`, `assets`
- **Ціни**: `tiers`, `options`, `audience_pricing`
- **Політики**: `pricing_policies`, `policy_runs`, `change_log`
- **Конфіги/замовлення**: `config_snapshots`, (згодом) `orders`, `payments`

## Іменування
- snake_case для таблиць/полів
- первинні ключі: текстові ID (сталі) або складені (для tiers: `(variant_id, qty_min)`)
- зовнішні ключі з cascade=restrict (уважно контролюємо видалення)

## JSONB стратегія
- Часті/критичні атрибути → окремі колонки (типізовані)
- Рідкі/експериментальні → `attributes: JSONB`
- Індекси: GIN (`jsonb_path_ops`) на часто фільтрованих шляхах

## Версіонування/майбутні ціни
- Поля `effective_from` (і, за потреби, `effective_to`)
- Запити беруть «актуальний» рядок на поточну дату

## Матеріалізовані в’юхи
- `catalog_from_price` — мінімальна ціна по варіанту/продукту
- Рефреш за графіком або після `policy_runs.completed`
