"""
Модуль для физики
Специфичная логика для физических заданий
"""
from .parser import PhysicsParser
from .checker import PhysicsChecker
from .. import register_parser, register_checker


def register():
    """Регистрация физического парсера и чекера"""
    register_parser('physics', PhysicsParser)
    register_checker('physics', PhysicsChecker)


__all__ = ['PhysicsParser', 'PhysicsChecker', 'register']

