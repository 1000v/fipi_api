"""
Чекер для русского языка
"""
from typing import Any

from ...subjects.default.checker import DefaultChecker
from ...models.task import Task, TaskType


class RussianChecker(DefaultChecker):
    """
    Чекер для русского языка
    
    Особенности:
    - Обработка текстовых ответов
    - Нормализация регистра (может быть важно)
    - Множественные правильные варианты
    """
    
    def format_answer(self, task: Task, user_input: Any) -> str:
        """
        Форматировать ответ с учетом специфики русского языка
        
        Args:
            task: Задание
            user_input: Ответ пользователя
        
        Returns:
            Отформатированная строка
        """
        # Для краткого ответа
        if task.task_type == TaskType.SHORT_ANSWER:
            return self._format_russian_short_answer(user_input)
        
        # Остальные типы - стандартная обработка
        return super().format_answer(task, user_input)
    
    def _format_russian_short_answer(self, user_input: Any) -> str:
        """
        Форматировать краткий ответ для русского языка
        
        Особенности:
        - Убираем лишние пробелы
        - Может быть чувствителен к регистру
        """
        answer = str(user_input).strip()
        
        # Убираем множественные пробелы
        import re
        answer = re.sub(r'\s+', ' ', answer)
        
        # Для последовательностей цифр (например, "12345")
        # оставляем как есть
        
        return answer
    
    def validate_answer_format(self, task: Task, user_input: Any) -> bool:
        """
        Валидация ответа для русского языка
        
        Args:
            task: Задание
            user_input: Ответ пользователя
        
        Returns:
            True если формат корректен
        """
        if task.task_type == TaskType.SHORT_ANSWER:
            answer_str = str(user_input).strip()
            
            # Любой непустой текст
            if len(answer_str) > 0:
                return True
            
            return False
        
        return super().validate_answer_format(task, user_input)

