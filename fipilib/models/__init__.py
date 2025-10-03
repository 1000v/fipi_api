"""
Модели данных
"""

from .task import Task, TaskType, AnswerVariant, MatchingOption, MatchingChoice
from .result import CheckResponse, CheckResult
from .config import SubjectConfig, SUBJECTS

__all__ = [
    'Task',
    'TaskType',
    'AnswerVariant',
    'MatchingOption',
    'MatchingChoice',
    'CheckResponse',
    'CheckResult',
    'SubjectConfig',
    'SUBJECTS'
]

