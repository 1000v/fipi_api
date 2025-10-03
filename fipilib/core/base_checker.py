"""
Базовый абстрактный класс для проверки заданий
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time

from ..models.task import Task, TaskType
from ..models.config import SubjectConfig
from ..models.result import CheckResponse, CheckResult
from .session_manager import SessionManager


class BaseChecker(ABC):
    """
    Абстрактный базовый чекер для всех предметов
    
    Реализует общую логику отправки запросов
    Предметы могут переопределить форматирование ответов
    """
    
    def __init__(self, config: SubjectConfig, cookie_file: Optional[str] = None, cookies: Optional[Dict] = None):
        """
        Args:
            config: Конфигурация предмета
            cookie_file: Путь к файлу с cookies (опционально)
            cookies: Словарь с cookies (опционально)
        """
        self.config = config
        self.session_manager = SessionManager(cookie_file=cookie_file, cookies=cookies)
        self.session = self.session_manager.get_session()
    
    def check_answer(self, task: Task, user_input: Any) -> CheckResponse:
        """
        Проверить ответ пользователя
        
        Args:
            task: Задание
            user_input: Ответ пользователя
        
        Returns:
            CheckResponse с результатом
        """
        # Форматируем ответ (может быть специфично для предмета)
        answer_str = self.format_answer(task, user_input)
        
        # Отправляем на проверку
        try:
            result_code = self._send_check_request(task.guid, answer_str)
            result = self._parse_result_code(result_code)
            
            return CheckResponse(
                guid=task.guid,
                task_id=task.task_id,
                result=result,
                user_answer=answer_str,
                result_code=result_code
            )
        
        except Exception as e:
            print(f"Ошибка при проверке: {e}")
            return CheckResponse(
                guid=task.guid,
                task_id=task.task_id,
                result=CheckResult.ERROR,
                user_answer=answer_str,
                error=str(e)
            )
    
    @abstractmethod
    def format_answer(self, task: Task, user_input: Any) -> str:
        """
        Форматировать ответ пользователя для отправки на сервер
        (специфично для предмета)
        
        Args:
            task: Задание
            user_input: Ответ пользователя
        
        Returns:
            Отформатированная строка ответа
        """
        pass
    
    def _send_check_request(self, guid: str, answer: str) -> str:
        """
        Отправить запрос на проверку
        
        Args:
            guid: GUID задания
            answer: Отформатированный ответ
        
        Returns:
            Код результата от сервера
        """
        url = f"{self.config.base_url}/bank/solve.php"
        
        # Используем multipart/form-data
        boundary = '---------------------------247746999627336697471839302941'
        
        body_parts = [
            f'--{boundary}',
            'Content-Disposition: form-data; name="guid"',
            '',
            guid,
            f'--{boundary}',
            'Content-Disposition: form-data; name="answer"',
            '',
            str(answer),
            f'--{boundary}',
            'Content-Disposition: form-data; name="ajax"',
            '',
            '1',
            f'--{boundary}',
            'Content-Disposition: form-data; name="proj"',
            '',
            self.config.project_id,
            f'--{boundary}--',
            ''
        ]
        
        body = '\r\n'.join(body_parts)
        
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Referer': f'{self.config.base_url}/bank/questions.php?proj={self.config.project_id}'
        }
        
        response = self.session.post(
            url,
            data=body.encode('utf-8'),
            headers=headers,
            timeout=self.config.request_timeout,
            verify=False
        )
        
        response.raise_for_status()
        time.sleep(self.config.request_delay)
        
        return response.text.strip()
    
    def _parse_result_code(self, code: str) -> CheckResult:
        """
        Преобразовать код ответа в CheckResult
        
        Args:
            code: Код от сервера
        
        Returns:
            CheckResult
        """
        code_map = {
            '1': CheckResult.CORRECT,
            '3': CheckResult.CORRECT,
            '2': CheckResult.INCORRECT,
            '0': CheckResult.ERROR
        }
        
        return code_map.get(code, CheckResult.ERROR)
    
    def validate_answer_format(self, task: Task, user_input: Any) -> bool:
        """
        Валидация формата ответа (может быть переопределено)
        
        Args:
            task: Задание
            user_input: Ответ пользователя
        
        Returns:
            True если формат корректен
        """
        return True

