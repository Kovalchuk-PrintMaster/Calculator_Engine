# API (v1)

## Роутери
- **/health** — перевірка живості (200, `{status, service, version, docs}`)
- **/meta**
  - `GET /meta/ping` → `{pong: true, ts: ISO8601}`
  - `GET /meta/info` → `{service, version, env, docs}`
- **/price**
  - `POST /price/quote` → `{unit_price, subtotal, vat, total, lead_time_days, breakdown}`

## Помилки
- 400 — семантична валідація (невідома `audience`, некоректний діапазон `qty`).
- 422 — структурна валідація (формат JSON/схема не збігається).
