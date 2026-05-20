так ще треба передбачити наступні моменти
у нас наш калькулятор скоріш завсе буде використовуватись в 2 варіантах перший це самостійний для продвинутих користувачів тому у нас має бути тежзакладений функціонал для авторизації і обліку користувачів 
друге для звичайних користувачів вони будуть мати або обмежений спрощений функціонал або взагалі калькулятор бачити не будуть вони будуть обирати стандартні товари на сайті (ми до ноього перейдемо наступним кроком піся калькулятора у мене вже деяка основа є) і зсайту на калькулятор буде прилітіти ордер з чіткими параметрами тому калькулятор має мати інтерфейс прийому таких автоматизованих прорахунків
після опрацювання замовлення калькулятор має вміти формувати 2 типи звіту перший це коли користувач напряму зайшов на калькулятор і він отримає людино зрозумілу форму з прорахунком де будуть вказани номер замовлення дата всі технічні параметри і таке інше другий варіант це форма яка буде повертатися на сайт щоб сайт міг вивести інформацію клієнту 
також треба продумати синхронізацію клієнтів  на сайті і в калькуляторі щоб не було задвоєнь і организувати легкий без повторної аутентифікації перехід між сайтом і калькулятором 
можливо на данному єтапі нема сенсу стрибати і відразу починати це реалізовувати але якщо фундаментально десь треба щось закласти в основу то треба тоді це зробити інше можемо просто поки прописати в Blueprint  і зафіксувати в план виконання на майбутнє коли доробимо тещо вже в роботі 

Що закладаємо вже зараз
1. Відокремлюємо calculation core від channels

Калькулятор має вміти працювати з двома джерелами запиту:

interactive/manual — користувач зайшов у калькулятор і руками збирає конфіг
external/order-import — сайт або інша система прислали готовий payload на прорахунок

Тобто ядро не повинно знати, звідки прийшов запит.
Йому треба давати уніфікований CalculationRequest.

2. Відразу вводимо поняття CalculationRequest / CalculationResult

Не як API-роут, а як окремий доменний контракт.

Мінімально:
CalculationRequest
- source: "manual" | "external"
- brand_code
- customer_ref
- external_order_id | None
- product_template_code
- material_code
- quantity
- selected_operation_codes
- locale
- currency
- input_payload_json
CalculationResult
- calculation_id
- source
- status
- route
- lines
- subtotal
- total
- currency
- technical_snapshot_json
- public_snapshot_json

Це критично, бо потім:

manual UI
сайт
admin
PDF/HTML report
усі будуть працювати поверх одного формату.
3. Відразу закладаємо ідемпотентність

Для інтеграції із сайтом це обов’язково.

Потрібні поля:

source_system
external_order_id
external_customer_id
idempotency_key

Щоб якщо сайт два рази відправив один і той самий ордер, калькулятор:

не створив дубль
а повернув уже існуючий результат
Що треба закласти по користувачах уже зараз
4. Не змішувати auth із customer data

Потрібно розділити:

Account

хто логіниться в калькулятор

CustomerProfile

бізнес-профіль клієнта

ExternalIdentityLink

зв’язок із сайтом / CRM / ERP

Приклад:

Account
- id
- email
- role
- active

CustomerProfile
- id
- account_id | null
- display_name
- phone
- company_name
- tax_id
- metadata_json

ExternalIdentityLink
- provider_code
- external_user_id
- external_customer_id
- customer_profile_id
- unique(provider_code, external_user_id)

Це прибере задвоєння між сайтом і калькулятором.

5. Для безшовного переходу сайт → калькулятор

Не треба окрему повторну аутентифікацію “логін ще раз”.

Правильний напрям:

або єдиний identity provider
або signed SSO token
або short-lived one-time access token

Для твоєї архітектури найпрактичніше потім буде:

сайт генерує короткоживучий підписаний токен
калькулятор його приймає
знаходить/створює ExternalIdentityLink
відкриває сесію без повторного логіну

Це не треба реалізовувати прямо зараз, але треба закласти окремий adapter layer для identity federation.

Що треба закласти по замовленнях уже зараз
6. Потрібен окремий ingestion layer

Не змішувати manual preview API і order import API.

Окремі режими:
/catalog/... — discovery / preview / quote
/intake/orders/... — прийом зовнішніх замовлень
/reports/... — видача результатів

Тобто сайт не має ходити в preview-роути як в основний production integration flow.

7. Потрібна окрема сутність CalculationJob

Навіть якщо поки все синхронне.

CalculationJob
- id
- source
- status
- brand_code
- customer_profile_id | null
- external_order_id | null
- request_payload_json
- normalized_request_json
- result_payload_json
- error_message
- created_at
- finished_at

Навіщо:

аудит
повторний перегляд результату
повторна генерація report
дебаг інтеграції із сайтом
Що треба закласти по звітах
8. Не робити “один report на всі випадки”

Потрібно одразу проектувати 2 проекції результату:

HumanQuoteReport

для прямого користувача

номер
дата
параметри
маршрут
пояснення
сума
валюта
notes
ExternalSiteQuoteResponse

для сайту

machine-readable
компактний
стабільний JSON-контракт
без зайвих пояснень
з codes/id/status

Тобто ядро рахує одне, а renderers роблять різні форми подачі.

Що я б не реалізовував прямо зараз

Оце поки в blueprint, але не в код:

повний auth flow
повний SSO
user кабинети
sync з сайтом
async job queue
PDF rendering
складний order lifecycle

Бо зараз це ще зарано.

Що я б реалізував уже на наступних етапах
Phase 1 — закласти доменні контракти

Оце я б робив наступним робочим пакетом:

CalculationRequest
CalculationResult
CalculationJob
ReportProjection interfaces
Phase 2 — external intake skeleton
POST /intake/orders/quote
idempotency
external_order_id
збереження CalculationJob
Phase 3 — user/customer skeleton
Account
CustomerProfile
ExternalIdentityLink
Phase 4 — SSO / bridge із сайтом
signed token
auto-link customer
seamless переходи
Моя рекомендація по фундаменту
Треба закласти вже зараз
CalculationRequest / CalculationResult
CalculationJob
розділення manual API vs external intake API
customer/account/external identity як окремі поняття
дві форми report projection
Можна поки лишити в blueprint
повний auth
SSO
sync клієнтів
PDF/HTML reports
асинхронну обробку
Найкращий наступний крок

Я б зараз не ліз у повний auth, а зробив foundation package для:

CalculationRequest
CalculationResult
CalculationJob
manual vs external source
report projections

