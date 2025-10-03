# FIPI Library v2.0 - Модульная библиотека для работы с Открытым банком ФИПИ

Современная, модульная и расширяемая Python библиотека для парсинга и проверки заданий из Открытого банка заданий ФИПИ.

## 🎯 Особенности

- **Модульная архитектура** - легко добавлять новые предметы
- **Специфика предметов** - каждый предмет имеет свою логику обработки
- **Базовые абстрактные классы** - единый интерфейс для всех предметов
- **Система плагинов** - регистрация новых парсеров и чекеров
- **Богатый функционал** - парсинг, проверка, сохранение, статистика

## 📦 Структура проекта

```
fipilib/
├── core/                   # Базовые абстрактные классы
│   ├── base_parser.py     # Абстрактный парсер
│   ├── base_checker.py    # Абстрактный чекер
│   └── session_manager.py # Управление HTTP-сессиями
├── subjects/              # Предметные модули
│   ├── default/          # Стандартная реализация
│   ├── physics/          # Физика
│   ├── math_prof/        # Математика (профиль)
│   └── russian/          # Русский язык
├── models/               # Модели данных
│   ├── task.py          # Модель задания
│   ├── result.py        # Модель результата
│   └── config.py        # Конфигурация предметов
└── utils/               # Утилиты
    ├── file_manager.py  # Работа с файлами
    └── answer_helpers.py # Вспомогательные функции
```

## 🚀 Установка

```bash
# Клонируйте репозиторий
git clone <url>
cd fipilib

# Установите зависимости
pip install -r requirements.txt
```

## 📖 Быстрый старт

### 1. Список доступных предметов

```python
from fipilib import list_subjects

subjects = list_subjects()
for subject in subjects:
    print(f"{subject['name']} ({subject['key']})")
```

### 2. Парсинг заданий

```python
from fipilib import get_parser

# Создаем парсер для физики
parser = get_parser('physics')

# Парсим одну страницу
tasks = parser.parse_and_save(page=0, page_size=10)

print(f"Найдено заданий: {len(tasks)}")
```

### 3. Проверка ответа

```python
from fipilib import get_checker
from fipilib.utils import FileManager

# Загружаем задание
fm = FileManager()
task_dirs = fm.find_tasks_by_subject('physics')
task = fm.load_task(task_dirs[0])

# Проверяем ответ
checker = get_checker('physics')
result = checker.check_answer(task, "35")

print(f"Результат: {result.result.value}")
```

## 🎓 Предметы

### Доступные предметы

| Предмет | Ключ | Особенности |
|---------|------|-------------|
| Физика | `physics` | Единицы измерения, формулы, графики |
| Математика (профиль) | `math_prof` | Формулы, дроби, чертежи |
| Русский язык | `russian` | Тексты, орфография, пунктуация |

### Добавление нового предмета

```python
from fipilib.subjects import register_parser, register_checker
from fipilib.subjects.default import DefaultParser, DefaultChecker
from fipilib.models.config import SubjectConfig, SUBJECTS

# 1. Добавляем конфигурацию
SUBJECTS['chemistry'] = SubjectConfig(
    subject_key='chemistry',
    project_id='YOUR_PROJECT_ID',
    display_name='Химия'
)

# 2. Создаем кастомные классы (или используем Default)
class ChemistryParser(DefaultParser):
    def post_process_task(self, task):
        # Специфичная логика для химии
        return task

# 3. Регистрируем
register_parser('chemistry', ChemistryParser)
register_checker('chemistry', DefaultChecker)
```

## 🔧 Архитектура

### Базовые классы

**BaseParser** - абстрактный класс для всех парсеров:
- `get_questions_page()` - получение HTML страницы
- `parse_page()` - парсинг всех заданий
- `parse_task_block()` - парсинг одного задания
- `parse_answer_block()` - парсинг блока ответов (абстрактный)
- `post_process_task()` - пост-обработка (переопределяется)

**BaseChecker** - абстрактный класс для всех чекеров:
- `check_answer()` - проверка ответа
- `format_answer()` - форматирование ответа (абстрактный)
- `validate_answer_format()` - валидация (переопределяется)

### Специфичные реализации

Каждый предмет может переопределить:
1. `parse_answer_block()` - если логика парсинга отличается
2. `post_process_task()` - для добавления метаданных
3. `format_answer()` - для специфичного форматирования
4. `validate_answer_format()` - для валидации ответов

## 📚 Примеры

Смотрите папку `examples/`:
- `basic_usage.py` - базовые примеры
- `advanced_usage.py` - продвинутые примеры

## 🔍 API Reference

### Основные функции

```python
# Получить парсер для предмета
parser = get_parser('physics')

# Получить чекер для предмета
checker = get_checker('math_prof')

# Список предметов
subjects = list_subjects()
```

### FileManager

```python
from fipilib.utils import FileManager

fm = FileManager()

# Сохранить задание
paths = fm.save_task(task)

# Загрузить задание
task = fm.load_task(task_dir)

# Найти задания
task_dirs = fm.find_tasks_by_subject('physics')

# Статистика
stats = fm.get_statistics()
```

### AnswerHelper

```python
from fipilib.utils import AnswerHelper

# Бинарная строка <-> индексы
indices = AnswerHelper.binary_string_to_indices("10101")
binary = AnswerHelper.indices_to_binary_string([0, 2, 4], 5)

# Соответствие
mapping = AnswerHelper.parse_matching_answer("2413")
string = AnswerHelper.format_matching_answer({"А": "2", "Б": "4"})
```

## 🎨 Типы заданий

1. **SHORT_ANSWER** - Краткий ответ (число/текст)
2. **MULTIPLE_CHOICE** - Множественный выбор (checkbox)
3. **MATCHING** - Установление соответствия (select)
4. **EXTENDED_ANSWER** - Развернутый ответ (для будущего использования)

## 📊 Форматы ответов

### Краткий ответ
```python
user_answer = "35"
# или
user_answer = "3.5"
```

### Множественный выбор
```python
# Список индексов (начиная с 0)
user_answer = [0, 2, 4]
# или бинарная строка
user_answer = "10101"
```

### Установление соответствия
```python
# Словарь
user_answer = {"А": "2", "Б": "4", "В": "1"}
# или список
user_answer = ["2", "4", "1"]
# или строка
user_answer = "241"
```

## 🤝 Вклад в проект

Библиотека спроектирована для легкого расширения:

1. Создайте папку `fipilib/subjects/your_subject/`
2. Реализуйте `YourParser(BaseParser)` и `YourChecker(BaseChecker)`
3. Зарегистрируйте в `__init__.py`
4. Добавьте конфигурацию в `models/config.py`

## ⚠️ Важные примечания

- Это неофициальное API
- ФИПИ может изменить структуру сайта в любой момент
- Используйте ответственно и соблюдайте правила сайта
- Между запросами автоматически добавляется задержка (1 сек)

## 📝 Лицензия

MIT License

## 🔗 Ссылки

- [Официальный сайт ФИПИ](https://fipi.ru/)
- [Открытый банк заданий](https://ege.fipi.ru/bank/)

## 📧 Контакты

Для вопросов и предложений создавайте Issue в репозитории.

---

**Версия:** 2.0.0  
**Дата обновления:** 2025  
**Статус:** Ленивая разработка

