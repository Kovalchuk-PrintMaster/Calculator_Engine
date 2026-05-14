Головний принцип

Не робимо так:

if product == "business_card": ...
if material == "tintoretto": ...
окремий Python-скрипт на кожен новий продукт

Робимо так:

у коді є стабільний движок
у БД є довідники, матриці сумісності, правила, формули, маршрути виробництва
адмінка керує тим, що можна, з чим можна, як рахується, які кроки виробництва потрібні

Тобто код знає:

що таке друк
що таке ламінація
що таке тиснення
що таке фольгування
що таке листовий матеріал
як збирати маршрут і рахувати собівартість

А от:

які саме матеріали існують
які з них сумісні з якими операціями
які продукти доступні
які комбінації дозволені
які прайси діють

це вже не код, а дані.

Правильна стратегія
1. Розділити систему на 3 рівні
Рівень 1 — стабільний кодовий движок

Його задача:

читати конфіг з БД
перевіряти сумісність
будувати виробничий маршрут
рахувати ціну
повертати доступні опції користувачу

Цей рівень змінюється рідко.

Рівень 2 — конфігурація в БД

Тут живе все, що часто змінюється:

матеріали
технології
операції
типи продуктів
правила сумісності
формули
прайси
параметри обладнання
обмеження

Це змінюється часто через адмінку.

Рівень 3 — інтерфейс адмінки

Адмінка не просто “довідник”, а конструктор виробничої логіки:

додати матеріал
вказати категорію
вказати параметри
відмітити доступні технології
задати правила сумісності
прив’язати формули/прайси
активувати для продуктів
Найважливіше архітектурне рішення
Не “скрипти на продукт”, а “ядро + модулі операцій”

Оце критично.

Поганий шлях

“На кожен продукт свій скрипт”.

Чому погано:

дублювання логіки
важко тестувати
важко підтримувати
новий продукт = новий код
стара логіка почне роз’їжджатися
Правильний шлях

У коді є універсальні модулі операцій:

print
lamination
foil
emboss
cutting
creasing
uv
white_print
eco_solvent
cnc
packing
etc.

І кожен продукт — це не окремий скрипт, а композиція операцій.

Тобто:

візитка = material + size + print + cut + optional lamination
бірка = material + print + hole + cut
коробка = material + print + crease + cut + glue
наклейка = film/paper + print + contour cut

Це означає:

новий продукт часто можна зібрати без нового коду
треба лише новий запис у БД і нову конфігурацію маршруту
Як має виглядати модель даних
1. Матеріали

Сутність Material

Поля:

code
name
category
subtype
thickness
density
width
height
roll/sheet
printable
adhesive
transparent
coated
price_source
active

Але чекбокси типу “можна друк / можна тиснення” я б не тримав просто полями в одній таблиці.

Краще так:

2. Технології / операції

Сутність OperationType

Наприклад:

digital_print
uv_print
eco_solvent_print
lamination
foil
emboss
contour_cut
die_cut
crease
3. Матриця сумісності

Сутність MaterialOperationCapability

Зв’язка:

material
operation_type
is_allowed
constraints_json / settings_json

Приклад:

Tintoretto + digital_print = allowed
Tintoretto + uv_print = allowed
Tintoretto + eco_solvent_print = not allowed
Tintoretto + foil = allowed
Tintoretto + emboss = allowed

Тут і живе твоя логіка “галочок”, але не як примітивні bool-поля, а як нормалізована таблиця сумісності.

Далі — продукти
4. Тип продукту

Сутність ProductType

Наприклад:

business_card
flyer
sticker
box
tag
certificate
5. Шаблон продукту

Сутність ProductTemplate

Вона описує:

до якого ProductType належить
які параметри конфігурації дозволені
які операції обов’язкові
які операції опціональні
які матеріали/категорії дозволені
які формули використовуються

Приклад:
business_card_standard

material_category: sheet_paper
required operations: cut
optional operations: lamination, foil, emboss
allowed print_types: digital_print, uv_print
size profile: business_card_sizes
Правила і валідатори

Оце серце системи.

6. Rules engine

Тобі потрібен не “if-else calculator”, а движок правил.

Є 3 типи правил:

A. Правила сумісності

“Що з чим можна”

Приклади:

roll material не можна для sheet-only product
foil allowed only if material supports foil
white_print only for transparent media
emboss not allowed below certain density
B. Правила маршруту

“Які виробничі кроки треба зібрати”

Приклад:

якщо обрано foil, додається operation step foil
якщо вибрано lamination, після print додається lamination
якщо форма нестандартна — додається contour_cut
C. Правила ціни

“Як рахувати”

Приклад:

друк = area × rate
ламінація = area × coefficient
фольга = setup + area × foil_rate
матеріал = quantity × sheet_cost × waste_factor
Як саме рахувати ціну
Не хардкодити формули на продукт

Код має рахувати по набору cost components.

Приклад моделі

Є PricingComponent:

material_cost
print_cost
setup_cost
finishing_cost
cut_cost
logistics_cost
markup
minimum_order_adjustment

І калькулятор працює так:

будує маршрут
для кожного кроку знаходить pricing rule
збирає cost items
сумує
додає націнку/ПДВ/округлення

Тобто продукт не має “свою формулу”, він має складений маршрут та набір правил.

Автолоадер — як це правильно реалізувати

Те, що ти називаєш автолоадером, я б реалізував так:

У коді є registry операцій

Наприклад:

operation handler registry
pricing handler registry
validation handler registry

Умовно:

digital_print → handler друку
foil → handler фольгування
emboss → handler тиснення
contour_cut → handler фігурної порізки

Коли в адмінці додається новий матеріал, код не пишеться заново.
Система просто бачить:

матеріал підтримує digital_print, foil, emboss
для продукту business_card ці операції допустимі
отже ці комбінації стають доступними користувачу

Тобто “autoload” — це не виконання довільних скриптів із БД, а:

читання конфігурації
зіставлення її з реєстром відомих механік
Це дуже важливо

Не дозволяй адмінці виконувати Python-код.
Ніяких “вписати формулу як Python” і “виконати eval”.

Тільки:

декларативні правила
whitelist операторів
JSON / DSL / таблиці / формульні блоки
Якою має бути адмінка
Не одна таблиця “Матеріали”

А пов’язана система керування.

Мінімум потрібні розділи:
Матеріали
тип
категорія
параметри
активність
Технології
друк
післядрукарка
різка
сервісні операції
Сумісність матеріалів і технологій
material ↔ operation
allowed
limits
примітки
Типи продуктів
базові категорії продуктів
Шаблони продуктів
що доступно для конкретного продукту
Правила маршрутизації
які операції додаються за яких умов
Правила ціни
які компоненти використовуються
які коефіцієнти
які мінімалки
які винятки
Прайс-джерела
ціна матеріалу
ціна друку
ціна фінішки
приладка
відходи
Як має виглядати користувацький сценарій
Приклад: додали Tintoretto
Адмін відкриває Materials
Створює матеріал Tintoretto Neve 300
Вказує:
category = designer_cardstock
sheet format
density = 300
active = true
У розділі Material Capabilities ставить:
digital_print = allowed
uv_print = allowed
foil = allowed
emboss = allowed
eco_solvent = not allowed
У розділі Material Pricing вносить ціну
Система:
автоматично додає матеріал у доступні джерела для відповідних продуктів
показує його там, де дозволені сумісні операції
будує доступні комбінації без нових правок коду

Оце і є правильна поведінка.

Де все ж буде код

Повністю без коду не вийде.
Але код має бути тільки в стабільних місцях.

Код потрібен для:
ядра калькулятора
registry operation handlers
rule evaluator
route builder
pricing engine
validators
projection/cache rebuild
admin signals / background sync
Код не повинен знати про конкретний Tintoretto

Він повинен знати лише:

material supports foil
product template allows foil
route for foil exists
pricing rule for foil exists
Що я раджу як цільову архітектуру
Шари
1. Catalog

Довідники:

materials
product types
sizes
finishing types
machines
vendors
2. Capability Matrix

Сумісності:

material ↔ operation
product ↔ operation
technology ↔ material category
3. Configuration Layer

Керує:

product templates
option groups
parameter schema
defaults
4. Route Builder

Збирає виробничий маршрут з обраної конфігурації

5. Pricing Engine

Рахує:

material cost
operation cost
setup cost
waste
markup
minimums
6. API/UI Projection

Готує:

що показати користувачу
які опції доступні
які комбінації валідні
яку ціну повернути
Що робити поетапно
Етап 1 — зафіксувати доменну модель

Спочатку не кодити “калькулятор”, а описати сутності:

Material
MaterialCategory
OperationType
MaterialOperationCapability
ProductType
ProductTemplate
ProductTemplateOperation
PricingRule
PriceSource
RouteRule
ConstraintRule

Це перший крок.

Етап 2 — описати канонічний flow

В одному документі:

user selection → validation → route build → pricing → response

Поки це не описано, писати код рано.

Етап 3 — зробити адмінські моделі для каталогу і сумісності

Не весь калькулятор одразу.
Спочатку:

матеріали
операції
сумісності
шаблони продуктів
Етап 4 — зробити engine доступних комбінацій

Ще без фінальної ціни.
Просто:

користувач вибирає продукт
система показує доступні матеріали
далі доступні операції
далі доступні параметри
Етап 5 — зробити route builder

На вході конфіг
На виході список operation steps

Етап 6 — зробити pricing engine

Калькуляція по кроках маршруту

Етап 7 — projection/cache

Щоб не рахувати все щоразу з нуля:

material capability cache
product availability projection
price preview cache
Що не можна пропустити
1. Валідація в адмінці

Адмін не повинен мати можливість створити абсурдну конфігурацію.

Потрібні перевірки:

матеріал без ціни не може бути active
продукт не може мати operation, для якої нема handler
pricing rule не може посилатися на неіснуючий cost component
route rule не може породжувати цикл
2. Versioning правил

Краще одразу думати про:

active_from
active_to
version
is_active

Щоб зміни правил не ламали старі прорахунки.

3. Audit trail

Хто змінив:

ціну
сумісність
маршрут
шаблон продукту
Моя чітка рекомендація
Не починати з “автолоадера матеріалів”

Починати треба з дизайну домену.

Бо якщо зараз просто почати “в адмінці поставимо чекбокси”, вийде хаос.

Правильний порядок:
описати сутності
описати зв’язки
описати flow
описати, що є стабільним кодом
тільки потім реалізація моделей і адмінки
Що я пропоную зробити прямо зараз

Я пропоную такий наступний практичний крок:

Сформувати технічний blueprint v1

У ньому буде:

список сутностей
зв’язки між ними
відповідальність кожної сутності
flow калькуляції
що живе в коді, а що в БД
що буде керуватись через адмінку

Після цього ми одразу зможемо перейти до:

проектування Django models
структури таблиць
адмінки
API flow

Якщо хочеш, наступним повідомленням я дам тобі готовий blueprint v1 у вигляді чіткої архітектурної схеми проекту, без води, вже як основу для реалізації.