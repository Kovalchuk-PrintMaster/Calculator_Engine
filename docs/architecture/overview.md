# Огляд архітектури

## Рівні
- **Frontend**: конструктор (Next.js/React), Telegram WebApp, згодом B2B-кабінет.
- **Backend**: FastAPI (API), Pricing Engine (розрахунок), Rules Engine (політики), файловий сервіс.
- **Дані**: PostgreSQL (ядро), Redis (кеш/черги), S3 (медіа/бекапи).
- **Адмінка**: HTMX/Jinja2 (політики, журнали змін, DIFF/rollback).
- **Інтеграції**: Telegram Bot/WebApp, платежі, email/SMS.

## Основні потоки
1) **/price/quote**: FE → API → (Redis?) → Pricing Engine → Postgres (tiers/options/audience) → відповідь `breakdown`.
2) **Масова зміна**: Адмін → політика → dry-run (DIFF) → apply (транзакція, change_log) → інвалідація кеша → нові ціни активні.
3) **Замовлення**: збереження конфігу → завантаження макетів (S3) → платіж → webhook → оновлення статусу.

## Принципи
- Єдине ядро ціноутворення для сайту/бота/WebApp.
- Пріоритет конфігів: `defaults < base.toml < {ENV}.toml < env`.
- Ключ кеша містить `rules_version`, щоб уникати застарілих цін.
- Бізнес-логіка в `domain/`, IO в `infra/`, API в `app/` — для тестованості та еволюції.
