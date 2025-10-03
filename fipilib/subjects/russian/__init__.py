"""
Модуль для русского языка
"""
from .parser import RussianParser
from .checker import RussianChecker
from .. import register_parser, register_checker


def register():
    """Регистрация парсера и чекера для русского языка"""
    register_parser('russian', RussianParser)
    register_checker('russian', RussianChecker)


__all__ = ['RussianParser', 'RussianChecker', 'register']

