"""
Конфигурация для работы с API ФИПИ
"""

# Базовый URL
BASE_URL = "https://ege.fipi.ru"

# API эндпоинты
QUESTIONS_ENDPOINT = "/bank/questions.php"
SOLVE_ENDPOINT = "/bank/solve.php"

# ID предметов
SUBJECTS = {
    "physics": {
        "id": "BA1F39653304A5B041B656915DC36B38",
        "name": "Физика",
        "name_en": "physics"
    },
    "math_prof": {
        "id": "AC437B34557F88EA4115D2F374B0A07B",
        "name": "Математика (профиль)",
        "name_en": "math_prof"
    }
}

# Типы заданий
TASK_TYPES = {
    "SHORT_ANSWER": "short_answer",      # Краткий ответ (текстовое поле)
    "MULTIPLE_CHOICE": "multiple_choice", # Множественный выбор (checkbox)
    "MATCHING": "matching"                # Установление соответствия (select)
}

# Коды результатов проверки
RESULT_CODES = {
    "1": "correct",           # Верно
    "2": "incorrect",         # Неверно
    "3": "partially_correct", # Частично верно
    "0": "error"              # Ошибка
}

# Настройки пагинации
DEFAULT_PAGE_SIZE = 10

# Директория для хранения данных
DATA_DIR = "data"

# Таймауты и задержки (в секундах)
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1.0  # Задержка между запросами

# Заголовки для запросов
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

