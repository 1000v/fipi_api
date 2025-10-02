"""
FIPI Parser & Checker
Система для парсинга и проверки заданий из Открытого банка ФИПИ
"""

__version__ = "1.0.0"

from .config import BASE_URL, SUBJECTS
from .models import Task, TaskType, CheckResult
from .parser import FIPIParser
from .checker import FIPIChecker, AnswerHelper
from .standalone_checker import StandaloneChecker, CookieManager, print_result
from .utils import FileManager

__all__ = [
    'BASE_URL',
    'SUBJECTS',
    'Task',
    'TaskType',
    'CheckResult',
    'FIPIParser',
    'FIPIChecker',
    'AnswerHelper',
    'StandaloneChecker',
    'CookieManager',
    'print_result',
    'FileManager',
]

