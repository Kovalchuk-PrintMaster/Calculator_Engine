Blueprint v1 — Calculator Engine
1. Мета

Побудувати data-driven калькулятор, у якому:

код описує механіку виробництва;
адмінка і БД описують продукти, матеріали, послуги, сумісності, маршрути, прайси, правила;
додавання нового матеріалу, продукту чи послуги не вимагає переписування ядра;
нові сутності підключаються через каталог + матриці сумісності + шаблони + правила.
2. Головний принцип
Код не знає конкретні продукти

Код не повинен містити:

if product == "business_card"
if material == "Tintoretto"
if service == "foil_gold"

Код повинен знати тільки:

що таке operation
що таке material
що таке product template
що таке capability
що таке route
що таке pricing component

Тобто:

дані відповідають на питання що доступно;
ядро відповідає на питання як це перевірити, зібрати і порахувати.
3. Цільова архітектура
3.1 Шари системи
A. Catalog Layer

Довідники та сутності предметної області.

Містить:

матеріали
категорії матеріалів
типи продуктів
шаблони продуктів
типи операцій
обладнання
постачальників
прайсові джерела
розміри
групи опцій
B. Capability Layer

Матриці сумісності.

Містить:

які операції доступні для матеріалу
які операції доступні для продукту
які технології дозволені для категорії матеріалу
які параметри доступні для шаблону продукту
C. Configuration Layer

Правила поведінки продуктів.

Містить:

шаблони продуктів
required / optional operations
параметри конфігурації
маршрутизаційні правила
валідатори
правила видимості опцій
D. Route Builder

Будує виробничий маршрут.

На вході:

продукт
матеріал
параметри користувача
вибрані опції

На виході:

послідовність операцій
контекст виконання
технологічні параметри
E. Pricing Engine

Рахує собівартість і ціну.

На вході:

маршрут
прайси
параметри тиражу
коефіцієнти
відходи
мінімалки
націнка

На виході:

breakdown
unit price
subtotal
total
technical notes
F. Projection / Availability Layer

Готує доступні користувачу варіанти.

На вході:

шаблон продукту
активні матеріали
матриці сумісності
правила

На виході:

які матеріали показати
які опції дозволити
які комбінації приховати
які значення дефолтні
G. Admin Layer

Інтерфейс керування конфігурацією системи.

4. Цільова логіка потоку
4.1 Runtime flow
Крок 1

Користувач обирає product_template

Крок 2

Система завантажує:

дозволені категорії матеріалів
доступні операції
параметри конфігурації
правила видимості
Крок 3

Користувач обирає:

матеріал
розмір
тип друку
опції
тираж
додаткові сервіси
Крок 4

Validation Engine перевіряє:

сумісність
обов’язкові параметри
бізнес-обмеження
технічні обмеження
Крок 5

Route Builder збирає маршрут:

print
lamination
foil
cut
pack
etc.
Крок 6

Pricing Engine рахує:

material cost
setup cost
operation cost
finishing cost
waste
markup
minimum adjustments
Крок 7

API повертає:

allowed config
warnings
route preview
price breakdown
total
5. Стабільне ядро коду

Оце те, що ми пишемо кодом і змінюємо рідко.

5.1 Operation Registry

Реєстр механік виробництва.

Приклади типів операцій:

digital_print
uv_print
eco_solvent_print
white_print
lamination
foil
emboss
contour_cut
die_cut
crease
glue
pack

Для кожного типу операції код знає:

як валідовати вхід
які параметри потрібні
як створити route step
як рахувати cost component
які технічні обмеження застосовуються
5.2 Validation Engine

Універсальний механізм перевірок.

Типи правил:

compatibility rules
parameter rules
material constraints
route constraints
pricing preconditions
5.3 Route Builder

Універсальний конструктор маршруту.

Він працює не від назви продукту, а від:

шаблону продукту
allowed operations
selected options
sequence rules
5.4 Pricing Engine

Універсальний калькулятор по компонентах.

Не “формула для візитки”, а:

material component
print component
finishing component
setup component
waste component
minimum order component
markup component
5.5 Projection Engine

Движок доступності опцій.

Показує користувачу тільки те, що:

активне
сумісне
валідне
доступне для конкретного шаблону
6. Те, що живе в БД і керується з адмінки
6.1 Materials

Матеріали та їх параметри.

Material

Базові поля:

code
name
category
subtype
form_factor: sheet / roll
density
thickness
width_mm
height_mm
printable
active
vendor
price_source
metadata_json
6.2 Operation Types

Довідник операцій.

OperationType

Поля:

code
name
group
handler_code
active
requires_setup
affects_area
affects_time
affects_waste
6.3 Material Capabilities

Матриця сумісності матеріалу з операціями.

MaterialOperationCapability

Поля:

material
operation_type
is_allowed
priority
constraints_json
notes
active

Це і є твоя логіка чекбоксів, але в нормалізованій формі.

6.4 Product Types

Базові типи продуктів.

ProductType

Поля:

code
name
group
active
6.5 Product Templates

Конкретні шаблони конфігурації продуктів.

ProductTemplate

Поля:

code
name
product_type
active
allowed_material_categories
parameter_schema_json
ui_schema_json
route_profile
pricing_profile
6.6 Product Template Operations

Операції, дозволені або обов’язкові для шаблону.

ProductTemplateOperation

Поля:

product_template
operation_type
is_required
is_optional
default_enabled
sequence_order
constraints_json
6.7 Pricing Sources

Джерела цін.

PriceSource

Поля:

code
name
source_type
active
currency
unit
metadata_json
6.8 Pricing Rules

Правила розрахунку.

PricingRule

Поля:

code
operation_type
product_type / template optional
material_category optional
formula_type
params_json
priority
active
valid_from
valid_to
6.9 Route Rules

Правила збирання маршруту.

RouteRule

Поля:

code
product_template
trigger_json
operation_type
insert_position
params_json
active
6.10 Constraint Rules

Обмеження та валідація.

ConstraintRule

Поля:

code
scope
target_type
condition_json
error_message
severity
active
7. Що таке “автолоадер” у правильному сенсі
Не виконання довільного коду

Не робимо:

eval
Python formulas from DB
dynamic script execution from admin
Робимо так

Коли адмін додає новий матеріал або новий продукт, система:

читає нові записи з БД;
звіряє їх із registry відомих operation handlers;
будує projection доступності;
кешує потрібні індекси;
робить нову конфігурацію доступною API.

Тобто “autoload” = перезбір доступних комбінацій на основі даних.

8. Мінімальні модулі коду, які потрібні
8.1 Catalog module

Завантаження і доступ до сутностей.

8.2 Capability service

Відповідає:

чи дозволена операція для матеріалу
чи дозволена операція для продукту
чи можна показувати опцію
8.3 Template resolver

Розв’язує:

який шаблон продукту вибраний
які параметри доступні
які опції показувати
8.4 Route builder

Збирає послідовність кроків.

8.5 Pricing calculator

Рахує ціну по компонентах.

8.6 Rule engine

Інтерпретує constraint / route / pricing rules.

8.7 Projection builder

Формує швидкі представлення для UI/API.

8.8 Admin sync hooks

Після змін у довідниках:

інвалідація кешу
rebuild projections
optional audit logging
9. Мінімальний контракт API
9.1 Отримати доступну конфігурацію продукту

Повертає:

allowed materials
allowed print types
allowed finishing
allowed sizes
parameter schema
9.2 Preview route

Повертає:

operations
warnings
technical notes
9.3 Quote

Повертає:

breakdown
total
lead time
selected route
10. Адмінка v1 — обов’язкові розділи

На першому етапі потрібні тільки ті розділи, без яких система не оживе.

Must-have
MaterialCategory
Material
OperationType
MaterialOperationCapability
ProductType
ProductTemplate
ProductTemplateOperation
PriceSource
PricingRule
RouteRule
ConstraintRule
Nice-to-have later
Machine
Vendor
Sheet format groups
Waste profiles
Lead time profiles
Customer segment modifiers
11. Правила проектування моделей
11.1 Все, що часто міняється — у БД

Якщо завтра це може змінитися без релізу, це не має бути хардкодом.

11.2 Все, що є механікою — у коді

Якщо це стабільна поведінка системи, це має бути handler/service/engine.

11.3 Без дублів логіки

Сумісність матеріалу й операції має жити в одному місці, а не:

частково в матеріалі
частково в продукті
частково в Python if
11.4 Версіонування правил

Потрібно закласти:

active
valid_from
valid_to
priority
11.5 Auditability

Критичні зміни мають бути видимі:

хто змінив ціну
хто дозволив нову операцію
хто активував новий шаблон
12. Що не робимо у v1

Щоб не розмазати систему.

Не робимо поки:
довільні формули як Python-код з адмінки
ML/AI підбір маршруту
надскладний DSL
багаторівневі workflow engine
повний ERP
Робимо тільки:
чіткий каталог
матрицю сумісності
шаблони продуктів
маршрут
розрахунок ціни
доступні комбінації
13. Реалізація по фазах
Phase 1 — Domain foundation

Завдання:

затвердити сутності
затвердити зв’язки
затвердити flow

Результат:

канонічна доменна модель
Phase 2 — Admin data model

Завдання:

створити Django models
підняти admin
створити базові зв’язки
seed базових operation types

Результат:

адмінка вже може описувати матеріали, операції, шаблони
Phase 3 — Capability engine

Завдання:

реалізувати сервіс сумісності
повернути доступні комбінації для продукту

Результат:

система вже знає, що можна вибирати
Phase 4 — Route builder

Завдання:

будувати кроки виробництва з конфігурації

Результат:

система вміє збирати технічний маршрут
Phase 5 — Pricing engine

Завдання:

рахувати breakdown і total

Результат:

перший реальний data-driven quote
Phase 6 — Projection/cache

Завдання:

прискорити response
кешувати availability і route previews

Результат:

швидка система для користувача
14. Перший практичний обсяг робіт

Ось із чого реально треба стартувати.

Sprint 1

Зробити тільки:

OperationType
MaterialCategory
Material
MaterialOperationCapability
ProductType
ProductTemplate
ProductTemplateOperation

І один простий сценарій:
business_card / flyer / poster без складних винятків.

Ціль sprint:

через адмінку додати матеріал
відмітити доступні операції
побачити через API доступні комбінації
без переписування коду під новий матеріал
15. Definition of Done для v1

Система вважається правильною, якщо:

новий матеріал додається через адмінку;
йому задаються allowed operations;
він автоматично стає доступним там, де сумісний;
користувач бачить тільки валідні комбінації;
маршрут збирається автоматично;
ціна рахується з БД-правил, а не з product-specific if-else.
16. Канонічна коротка формула проекту
Код

engine + handlers + validators + builders

БД

catalog + capabilities + templates + rules + prices

Адмінка

керування доступністю, сумісністю, маршрутом і прайсами

17. Наступний крок

Починати треба не з коду API, а з доменної схеми сутностей v1.

Тобто наступний практичний артефакт має бути:

Domain Model Spec v1

де ми формально пропишемо:

список моделей
поля
зв’язки
унікальності
індекси
які з них Django-admin editable
які з них engine-only
