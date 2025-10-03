"""
Модели для результатов проверки
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CheckResult(Enum):
    """Результаты проверки"""
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIALLY_CORRECT = "partially_correct"
    ERROR = "error"


@dataclass
class CheckResponse:
    """Результат проверки задания"""
    guid: str
    task_id: str
    result: CheckResult
    user_answer: str
    result_code: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'guid': self.guid,
            'task_id': self.task_id,
            'result': self.result.value,
            'user_answer': self.user_answer,
            'result_code': self.result_code,
            'error': self.error
        }
    
    def is_correct(self) -> bool:
        """Проверить, правильный ли ответ"""
        return self.result == CheckResult.CORRECT

