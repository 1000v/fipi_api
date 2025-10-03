"""
Стандартный чекер для предметов
"""
from typing import Any

from ...core.base_checker import BaseChecker
from ...models.task import Task, TaskType


class DefaultChecker(BaseChecker):
    """Стандартная реализация чекера"""
    
    def format_answer(self, task: Task, user_input: Any) -> str:
        """
        Форматировать ответ пользователя
        
        Args:
            task: Задание
            user_input: Ответ пользователя
        
        Returns:
            Отформатированная строка
        """
        if task.task_type == TaskType.SHORT_ANSWER:
            return self._format_short_answer(user_input)
        
        elif task.task_type == TaskType.MULTIPLE_CHOICE:
            return self._format_multiple_choice(task, user_input)
        
        elif task.task_type == TaskType.MATCHING:
            return self._format_matching(user_input)
        
        return str(user_input)
    
    def _format_short_answer(self, user_input: Any) -> str:
        """Форматировать краткий ответ"""
        return str(user_input).strip()
    
    def _format_multiple_choice(self, task: Task, user_input: Any) -> str:
        """Форматировать множественный выбор"""
        if isinstance(user_input, str):
            # Уже в формате бинарной строки
            return user_input
        
        # user_input - список индексов
        num_variants = len(task.answer_variants) if task.answer_variants else 5
        answer_bits = ['0'] * num_variants
        
        for idx in user_input:
            if 0 <= idx < num_variants:
                answer_bits[idx] = '1'
        
        return ''.join(answer_bits)
    
    def _format_matching(self, user_input: Any) -> str:
        """Форматировать установление соответствия"""
        if isinstance(user_input, str):
            return user_input
        
        # user_input - словарь {буква: номер}
        if isinstance(user_input, dict):
            sorted_letters = sorted(user_input.keys())
            return ''.join(str(user_input[letter]) for letter in sorted_letters)
        
        # user_input - список номеров
        elif isinstance(user_input, (list, tuple)):
            return ''.join(str(x) for x in user_input)
        
        return str(user_input)

