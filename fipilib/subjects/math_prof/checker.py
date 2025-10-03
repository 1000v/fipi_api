"""
Чекер для профильной математики
"""
from typing import Any
import re

from ...subjects.default.checker import DefaultChecker
from ...models.task import Task, TaskType


class MathProfChecker(DefaultChecker):
    """
    Чекер для профильной математики
    
    Особенности:
    - Нормализация числовых ответов
    - Обработка дробей
    - Точность вычислений
    """
    
    def format_answer(self, task: Task, user_input: Any) -> str:
        """
        Форматировать ответ с учетом специфики математики
        
        Args:
            task: Задание
            user_input: Ответ пользователя
        
        Returns:
            Отформатированная строка
        """
        # Для краткого ответа - нормализуем число
        if task.task_type == TaskType.SHORT_ANSWER:
            return self._format_math_short_answer(user_input)
        
        # Остальные типы - стандартная обработка
        return super().format_answer(task, user_input)
    
    def _format_math_short_answer(self, user_input: Any) -> str:
        """
        Форматировать краткий ответ для математики
        
        Особенности:
        - Убираем пробелы
        - Нормализуем десятичные разделители
        - Обрабатываем дроби
        """
        answer = str(user_input).strip()
        
        # Заменяем запятую на точку
        answer = answer.replace(',', '.')
        
        # Убираем пробелы
        answer = answer.replace(' ', '')
        
        # Обработка дробей (1/2 остается 1/2)
        
        return answer
    
    def validate_answer_format(self, task: Task, user_input: Any) -> bool:
        """
        Валидация ответа для математики
        
        Args:
            task: Задание
            user_input: Ответ пользователя
        
        Returns:
            True если формат корректен
        """
        if task.task_type == TaskType.SHORT_ANSWER:
            answer_str = str(user_input).strip()
            
            # Число (целое или десятичное)
            if re.match(r'^-?\d+([.,]\d+)?$', answer_str):
                return True
            
            # Дробь (1/2, -3/4)
            if re.match(r'^-?\d+/\d+$', answer_str):
                return True
            
            # Последовательность чисел (12345)
            if re.match(r'^\d+$', answer_str):
                return True
            
            return False
        
        return super().validate_answer_format(task, user_input)

