"""
Парсер для русского языка
"""
from ...subjects.default.parser import DefaultParser
from ...models.task import Task


class RussianParser(DefaultParser):
    """
    Парсер для русского языка
    
    Особенности:
    - Работа с текстами
    - Задания с несколькими правильными ответами
    - Орфография и пунктуация
    """
    
    def post_process_task(self, task: Task) -> Task:
        """
        Специфичная обработка для русского языка
        
        Args:
            task: Задание
        
        Returns:
            Обработанное задание
        """
        # Определяем тип задания по КЭС
        if task.kes_codes:
            task.metadata['russian_topic'] = self._classify_russian_topic(task.kes_codes)
        
        # Проверяем наличие исходного текста
        if len(task.question_text) > 500:
            task.metadata['has_source_text'] = True
        
        # Для множественного выбора - отмечаем количество вариантов
        if task.answer_variants:
            task.metadata['variant_count'] = len(task.answer_variants)
        
        return task
    
    def _classify_russian_topic(self, kes_codes: list) -> str:
        """
        Классифицировать тему русского языка
        
        Args:
            kes_codes: Коды КЭС
        
        Returns:
            Тема
        """
        if not kes_codes:
            return 'unknown'
        
        first_code = kes_codes[0].lower()
        
        if 'орфография' in first_code:
            return 'spelling'
        elif 'пунктуация' in first_code:
            return 'punctuation'
        elif 'синтаксис' in first_code:
            return 'syntax'
        elif 'морфология' in first_code:
            return 'morphology'
        elif 'лексика' in first_code:
            return 'lexicon'
        elif 'стилистика' in first_code:
            return 'style'
        else:
            return 'other'

