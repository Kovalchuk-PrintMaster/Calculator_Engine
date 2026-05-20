Blueprint наступного кроку---
1. Нові Pydantic-схеми для external intake

Створюємо файл:

apps/api/backend/calculator_engine/app/schemas/intake_v1.py

Там буде:

ExternalClientMetaSchema
ExternalQuoteIntakeDataV1
ExternalQuoteIntakeRequestV1
2. Mapper із зовнішнього контракту у внутрішній payload

Створюємо:

apps/api/backend/calculator_engine/app/services/intake_request_mapper.py

Задача:

прийняти ExternalQuoteIntakeRequestV1
зібрати звичний internal payload для process_quote_intake(...)
3. Intake router підтримує 2 режими

У intake.py:

або старий flat JSON
або новий envelope schema_version=v1

Це дозволить не ламати те, що вже працює.

4. Зберігаємо client metadata

У request_payload_json / audit payload зберігати:

channel=web/mobile/site
device=mobile/desktop
schema_version=v1

Це потім стане в пригоді:

для аналітики,
для mobile-UX,
для окремих policy.
5. Тести

Додаємо:

intake через schema_version=v1
intake через device=mobile
backward compatibility для старого flat payload
Що важливо для mobile вже зараз

Це частково фронт, але бекенд теж треба закласти правильно.

На бекенді для мобільного клієнта нам потрібні:

стабільний короткий request/response contract;
маленькі JSON-відповіді;
покрокові endpoint-и;
можливість відправляти неповний контекст клієнта;
явне поле device / channel.

Тобто mobile ми зараз не верстаємо, але API основу під mobile уже варто закладати.

Пропоную такий порядок реалізації
external intake request schema v1
backward compatibility
client.channel + client.device
тести
після цього — step-based mobile-friendly flow:
список шаблонів
список матеріалів
preview
quote
report
Стартуємо саме так

Наступним повідомленням я дам тобі готовий пакет файлів для intake request schema v1:

schemas/intake_v1.py
services/intake_request_mapper.py
правки в routers/intake.py
нові тести