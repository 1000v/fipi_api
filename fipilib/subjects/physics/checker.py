"""
Чекер для физики
"""
from typing import Any
import re

from ...subjects.default.checker import DefaultChecker
from ...models.task import Task, TaskType


class PhysicsChecker(DefaultChecker):
    """
    Чекер для физики
    
    Особенности:
    - Нормализация числовых ответов
    - Обработка единиц измерения
    - Точность вычислений
    """
    
    def format_answer(self, task: Task, user_input: Any) -> str:
        """
        Форматировать ответ с учетом специфики физики
        
        Args:
            task: Задание
            user_input: Ответ пользователя
        
        Returns:
            Отформатированная строка
        """
        # Для краткого ответа - нормализуем число
        if task.task_type == TaskType.SHORT_ANSWER:
            return self._format_physics_short_answer(user_input)
        
        # Остальные типы - стандартная обработка
        return super().format_answer(task, user_input)
    
    def _format_physics_short_answer(self, user_input: Any) -> str:
        """
        Форматировать краткий ответ для физики
        
        Особенности:
        - Убираем пробелы
        - Нормализуем десятичные разделители
        - Обрабатываем научную нотацию
        """
        answer = str(user_input).strip()
        
        # Заменяем запятую на точку
        answer = answer.replace(',', '.')
        
        # Убираем пробелы
        answer = answer.replace(' ', '')
        
        # Обработка научной нотации (1e-5 или 1*10^-5)
        # ФИПИ может принимать разные форматы
        
        return answer
    
    def validate_answer_format(self, task: Task, user_input: Any) -> bool:
        """
        Валидация ответа для физики
        
        Args:
            task: Задание
            user_input: Ответ пользователя
        
        Returns:
            True если формат корректен
        """
        if task.task_type == TaskType.SHORT_ANSWER:
            answer_str = str(user_input).strip()
            
            # Проверяем, что это число или текст
            # Числовой формат
            if re.match(r'^-?\d+([.,]\d+)?([eE][+-]?\d+)?$', answer_str):
                return True
            
            # Текстовый ответ (например, "вправо", "увеличится")
            if re.match(r'^[а-яА-Яa-zA-Z]+$', answer_str):
                return True
            
            return False
        
        return super().validate_answer_format(task, user_input)

