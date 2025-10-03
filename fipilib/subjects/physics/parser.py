"""
Парсер для физики
Учитывает специфику физических заданий
"""
from ...subjects.default.parser import DefaultParser
from ...models.task import Task


class PhysicsParser(DefaultParser):
    """
    Парсер для физики
    
    Особенности:
    - Единицы измерения (м, м/с, Дж и т.д.)
    - Формулы в LaTeX/MathML
    - Графики и диаграммы
    """
    
    def post_process_task(self, task: Task) -> Task:
        """
        Специфичная обработка для физики
        
        Args:
            task: Задание
        
        Returns:
            Обработанное задание
        """
        # Сохраняем информацию о единицах измерения в метаданные
        if task.answer_unit:
            task.metadata['unit_type'] = self._classify_unit(task.answer_unit)
        
        # Проверяем наличие формул
        if 'm:math' in task.question_html or '$$' in task.question_html:
            task.metadata['has_formulas'] = True
        
        # Проверяем наличие графиков
        if task.images:
            task.metadata['image_count'] = len(task.images)
            task.metadata['likely_has_graph'] = any(
                'graph' in img.lower() or 'diagram' in img.lower() 
                for img in task.images
            )
        
        return task
    
    def _classify_unit(self, unit: str) -> str:
        """
        Классифицировать единицу измерения
        
        Args:
            unit: Единица измерения
        
        Returns:
            Тип единицы (length, velocity, energy и т.д.)
        """
        unit_types = {
            'length': ['м', 'см', 'км', 'мм'],
            'velocity': ['м/с', 'км/ч'],
            'acceleration': ['м/с²', 'м/с2'],
            'force': ['Н', 'кН'],
            'energy': ['Дж', 'кДж', 'МДж', 'эВ', 'кэВ', 'МэВ'],
            'power': ['Вт', 'кВт', 'МВт'],
            'mass': ['кг', 'г', 'т'],
            'time': ['с', 'мс', 'мин', 'ч'],
            'temperature': ['°C', 'K', 'К'],
            'angle': ['°', 'рад'],
        }
        
        for type_name, units in unit_types.items():
            if unit in units:
                return type_name
        
        return 'other'

