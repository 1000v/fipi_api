"""
Парсер для профильной математики
"""
from ...subjects.default.parser import DefaultParser
from ...models.task import Task


class MathProfParser(DefaultParser):
    """
    Парсер для профильной математики
    
    Особенности:
    - Математические формулы и выражения
    - Координатные плоскости
    - Геометрические фигуры
    """
    
    def post_process_task(self, task: Task) -> Task:
        """
        Специфичная обработка для математики
        
        Args:
            task: Задание
        
        Returns:
            Обработанное задание
        """
        # Определяем тип математической задачи по КЭС
        if task.kes_codes:
            task.metadata['math_topic'] = self._classify_math_topic(task.kes_codes)
        
        # Проверяем наличие формул
        if 'm:math' in task.question_html or '$$' in task.question_html:
            task.metadata['has_formulas'] = True
        
        # Проверяем наличие графиков/чертежей
        if task.images:
            task.metadata['has_visual'] = True
            task.metadata['image_count'] = len(task.images)
        
        return task
    
    def _classify_math_topic(self, kes_codes: list) -> str:
        """
        Классифицировать тему математики
        
        Args:
            kes_codes: Коды КЭС
        
        Returns:
            Тема (algebra, geometry, calculus и т.д.)
        """
        if not kes_codes:
            return 'unknown'
        
        # Берем первый код
        first_code = kes_codes[0].lower()
        
        # Простая классификация по первой цифре/слову
        if 'алгебра' in first_code or 'уравнение' in first_code:
            return 'algebra'
        elif 'геометрия' in first_code or 'треугольник' in first_code or 'окружность' in first_code:
            return 'geometry'
        elif 'производная' in first_code or 'интеграл' in first_code:
            return 'calculus'
        elif 'функция' in first_code:
            return 'functions'
        elif 'вероятность' in first_code or 'статистика' in first_code:
            return 'probability'
        else:
            return 'other'

