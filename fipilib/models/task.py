"""
Модели для заданий
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class TaskType(Enum):
    """Типы заданий"""
    SHORT_ANSWER = "short_answer"
    MULTIPLE_CHOICE = "multiple_choice"
    MATCHING = "matching"
    EXTENDED_ANSWER = "extended_answer"  # Для развернутых ответов


@dataclass
class AnswerVariant:
    """Вариант ответа для задания с выбором"""
    index: int
    text: str
    input_name: str


@dataclass
class MatchingOption:
    """Опция для задания на соответствие"""
    letter: str
    text: str
    select_name: str


@dataclass
class MatchingChoice:
    """Вариант выбора для соответствия"""
    number: str
    text: str


@dataclass
class Task:
    """Модель задания"""
    guid: str
    task_id: str
    subject: str
    task_type: TaskType
    question_text: str
    question_html: str
    
    # Варианты ответов
    answer_variants: Optional[List[AnswerVariant]] = None
    matching_options: Optional[List[MatchingOption]] = None
    matching_choices: Optional[List[MatchingChoice]] = None
    
    # Для краткого ответа
    answer_unit: Optional[str] = None
    
    # Медиафайлы
    images: List[str] = field(default_factory=list)
    
    # КЭС (Кодификатор элементов содержания)
    kes_codes: List[str] = field(default_factory=list)
    
    # Метаданные (для специфичной информации предмета)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Конвертация в словарь"""
        data = asdict(self)
        data['task_type'] = self.task_type.value
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """Конвертация в JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Создание из словаря"""
        data = data.copy()
        data['task_type'] = TaskType(data['task_type'])
        
        if data.get('answer_variants'):
            data['answer_variants'] = [
                AnswerVariant(**v) for v in data['answer_variants']
            ]
        
        if data.get('matching_options'):
            data['matching_options'] = [
                MatchingOption(**o) for o in data['matching_options']
            ]
        
        if data.get('matching_choices'):
            data['matching_choices'] = [
                MatchingChoice(**c) for c in data['matching_choices']
            ]
        
        return cls(**data)

