"""
Стандартная реализация парсера и чекера
Работает для большинства предметов
"""
from .parser import DefaultParser
from .checker import DefaultChecker


def register():
    """Регистрация не требуется - используется как fallback"""
    pass


__all__ = ['DefaultParser', 'DefaultChecker']

