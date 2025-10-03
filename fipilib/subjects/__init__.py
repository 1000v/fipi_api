"""
Предметные модули с специфичной логикой
"""
from typing import Dict, Type, Optional
from ..core.base_parser import BaseParser
from ..core.base_checker import BaseChecker
from ..models.config import get_subject_config, SUBJECTS

# Регистр парсеров и чекеров
_PARSERS: Dict[str, Type[BaseParser]] = {}
_CHECKERS: Dict[str, Type[BaseChecker]] = {}


def register_parser(subject_key: str, parser_class: Type[BaseParser]):
    """Зарегистрировать парсер для предмета"""
    _PARSERS[subject_key] = parser_class


def register_checker(subject_key: str, checker_class: Type[BaseChecker]):
    """Зарегистрировать чекер для предмета"""
    _CHECKERS[subject_key] = checker_class


def get_parser(subject_key: str, cookie_file: Optional[str] = None, cookies: Optional[Dict[str, str]] = None) -> BaseParser:
    """
    Получить парсер для предмета
    
    Args:
        subject_key: Ключ предмета
        cookie_file: Путь к файлу с cookies (опционально)
        cookies: Словарь с cookies (опционально)
    
    Returns:
        Экземпляр парсера
    """
    config = get_subject_config(subject_key)
    
    if subject_key in _PARSERS:
        parser_class = _PARSERS[subject_key]
        return parser_class(config, cookie_file=cookie_file, cookies=cookies)
    
    # Fallback - используем стандартный парсер
    from .default.parser import DefaultParser
    return DefaultParser(config, cookie_file=cookie_file, cookies=cookies)


def get_checker(subject_key: str, cookie_file: Optional[str] = None, cookies: Optional[Dict[str, str]] = None) -> BaseChecker:
    """
    Получить чекер для предмета
    
    Args:
        subject_key: Ключ предмета
        cookie_file: Путь к файлу с cookies (опционально)
        cookies: Словарь с cookies (опционально)
    
    Returns:
        Экземпляр чекера
    """
    config = get_subject_config(subject_key)
    
    if subject_key in _CHECKERS:
        checker_class = _CHECKERS[subject_key]
        return checker_class(config, cookie_file=cookie_file, cookies=cookies)
    
    # Fallback - используем стандартный чекер
    from .default.checker import DefaultChecker
    return DefaultChecker(config, cookie_file=cookie_file, cookies=cookies)


def list_subjects() -> list:
    """Список доступных предметов"""
    return [
        {
            'key': key,
            'name': config.display_name,
            'has_custom_parser': key in _PARSERS,
            'has_custom_checker': key in _CHECKERS
        }
        for key, config in SUBJECTS.items()
    ]


# Импортируем предметные модули для автоматической регистрации
from .physics import register as register_physics
from .math_prof import register as register_math_prof
from .russian import register as register_russian
from .default import register as register_default

# Регистрация
register_physics()
register_math_prof()
register_russian()
register_default()

__all__ = ['get_parser', 'get_checker', 'list_subjects', 'register_parser', 'register_checker']

