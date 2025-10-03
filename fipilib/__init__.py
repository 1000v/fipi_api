"""
FIPI Library - Модульная библиотека для работы с Открытым банком ФИПИ

Архитектура:
- core: Базовые абстрактные классы
- subjects: Специфичные реализации для каждого предмета
- models: Модели данных
- utils: Вспомогательные утилиты
"""

__version__ = "2.0.0"
__author__ = "FIPI Library Team"

from .core.base_parser import BaseParser
from .core.base_checker import BaseChecker
from .models.task import Task, TaskType
from .models.result import CheckResult
from .subjects import get_parser, get_checker, list_subjects

__all__ = [
    'BaseParser',
    'BaseChecker',
    'Task',
    'TaskType',
    'CheckResult',
    'get_parser',
    'get_checker',
    'list_subjects',
]

