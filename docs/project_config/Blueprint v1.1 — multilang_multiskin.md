Оновлений Blueprint v1.1
Core domain
MaterialCategory
Material
OperationType
MaterialOperationCapability
ProductType
ProductTemplate
ProductTemplateOperation
UI / presentation domain
UiSkin
UiBrand
UiBrandProductTemplateVisibility
UiBrandMaterialVisibility ← можна додати трохи пізніше
Як саме міняємо моделі зараз

Я раджу не викидати одразу name_uk, а зробити безпечний перехід:

На найближчий крок

Додаємо в core-моделі:

name_i18n = JSONField(default=dict, blank=True)
description_i18n = JSONField(default=dict, blank=True)

і тимчасово залишаємо:

name_uk
description

Потім:

робимо data migration
переводимо admin/UI на *_i18n
і лише після цього прибираємо старі plain-text поля

Це акуратніше, ніж ламати все одразу.

Які моделі зачіпаємо під i18n

На цьому кроці:

1. ProductType

додаємо:

name_i18n
description_i18n
2. MaterialCategory

додаємо:

name_i18n
description_i18n
3. Material

додаємо:

name_i18n
4. OperationType

додаємо:

name_i18n
description_i18n
5. ProductTemplate

додаємо:

name_i18n
description_i18n
Як це має працювати в коді

Для всіх цих моделей вводимо просте правило доступу:

display helper

У моделі або shared helper:

def get_i18n_value(data: dict, locale: str, fallback: str = "uk") -> str:
    if not isinstance(data, dict):
        return ""
    return data.get(locale) or data.get(fallback) or next(iter(data.values()), "")

І далі:

API повертає назву в потрібній мові
адмінка поки може показувати name_uk
пізніше перейдемо на повноцінні i18n widgets
Multiskin v1 — поки тільки схема, без реалізації UI
1. UiSkin

Поля:

code
name
active
theme_json
2. UiBrand

Поля:

code
name
default_locale
default_skin
active
settings_json
3. UiBrandProductTemplateVisibility

Поля:

brand
product_template
is_visible
sort_order
default_enabled
Навіщо

Щоб один бренд/ринок бачив:

тільки свої продукти
свої дефолти
свої теми
свої тексти

Але це не чіпає калькуляторне ядро.

Що я рекомендую як наступний практичний крок
Sprint 1A — завершення core foundation

Зараз добиваємо:

нормалізацію admin під нові core-моделі
базові seed-дані
перший сервіс:
get_available_operations(product_template, material)
Sprint 1B — i18n foundation

Одразу після цього:

додаємо name_i18n, description_i18n
робимо migration
робимо helper для локалізованого display
Sprint 1C — skin/domain spec

Після стабілізації core:

додаємо UiSkin
UiBrand
UiBrandProductTemplateVisibility
Мій чіткий висновок

Зараз не стрибаємо одразу в multiskin-код, а робимо в правильному порядку:

добиваємо core admin і seed
робимо availability service
додаємо i18n поля в core-моделі
окремим блоком проектуємо brand/skin layer

Це дасть:

не зламати фундамент
не змішати presentation з pricing core
не переписувати двічі
Що робимо прямо зараз

Я пропоную такий наступний пакет:

Пакет 1
базовий seed для:
OperationType
MaterialCategory
ProductType
сервіс:
get_available_operations(product_template, material)