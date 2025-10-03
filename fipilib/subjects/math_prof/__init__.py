"""
Модуль для профильной математики
"""
from .parser import MathProfParser
from .checker import MathProfChecker
from .. import register_parser, register_checker


def register():
    """Регистрация парсера и чекера для математики"""
    register_parser('math_prof', MathProfParser)
    register_checker('math_prof', MathProfChecker)


__all__ = ['MathProfParser', 'MathProfChecker', 'register']

