"""
Core модуль - базовые абстрактные классы и общая логика
"""

from .base_parser import BaseParser
from .base_checker import BaseChecker
from .session_manager import SessionManager

__all__ = ['BaseParser', 'BaseChecker', 'SessionManager']

