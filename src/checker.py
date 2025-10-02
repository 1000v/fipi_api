"""
Модуль для проверки решений заданий ФИПИ
"""
import time
from typing import Optional, Dict, Any
import requests
import urllib3

# Отключение предупреждений о SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .config import (
    BASE_URL, SOLVE_ENDPOINT, SUBJECTS,
    REQUEST_TIMEOUT, REQUEST_DELAY, HEADERS, RESULT_CODES
)
from .models import Task, TaskType, CheckResult, CheckResponse


class FIPIChecker:
    """Проверка решений заданий ФИПИ"""
    
    def __init__(self, subject_key: str):
        """
        Инициализация checker'а
        
        Args:
            subject_key: Ключ предмета из SUBJECTS ('physics' или 'math_prof')
        """
        if subject_key not in SUBJECTS:
            raise ValueError(f"Неизвестный предмет: {subject_key}")
        
        self.subject_info = SUBJECTS[subject_key]
        self.project_id = self.subject_info['id']
        self.subject_name = self.subject_info['name_en']
        
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def format_answer_for_check(self, task: Task, user_input: Any) -> str:
        """
        Форматировать ответ пользователя в строку для отправки на сервер
        
        Args:
            task: Объект задания
            user_input: Ввод пользователя (формат зависит от типа задания)
        
        Returns:
            Отформатированная строка ответа
        
        Примеры:
            - Краткий ответ: user_input="35" -> return "35"
            - Множественный выбор: user_input=[0, 2] -> return "10100" (выбраны 1-й и 3-й)
            - Соответствие: user_input={"А": "2", "Б": "4"} -> return "24"
        """
        if task.task_type == TaskType.SHORT_ANSWER:
            # Краткий ответ - просто строка
            return str(user_input).strip()
        
        elif task.task_type == TaskType.MULTIPLE_CHOICE:
            # Множественный выбор - бинарная строка
            if not task.answer_variants:
                raise ValueError("Нет вариантов ответа для задания")
            
            # user_input - список индексов выбранных вариантов
            if isinstance(user_input, str):
                # Если уже в формате бинарной строки
                return user_input
            
            # Формируем бинарную строку
            num_variants = len(task.answer_variants)
            answer_bits = ['0'] * num_variants
            
            for idx in user_input:
                if 0 <= idx < num_variants:
                    answer_bits[idx] = '1'
            
            return ''.join(answer_bits)
        
        elif task.task_type == TaskType.MATCHING:
            # Установление соответствия - конкатенация выбранных значений
            if isinstance(user_input, str):
                # Если уже в формате строки
                return user_input
            
            # user_input - словарь {буква: номер}
            # Сортируем по буквам и склеиваем номера
            if isinstance(user_input, dict):
                sorted_letters = sorted(user_input.keys())
                return ''.join(str(user_input[letter]) for letter in sorted_letters)
            
            # user_input - список номеров в порядке А, Б, ...
            elif isinstance(user_input, (list, tuple)):
                return ''.join(str(x) for x in user_input)
        
        return str(user_input)
    
    def check_answer(self, task: Task, user_input: Any) -> CheckResponse:
        """
        Отправить ответ на проверку
        
        Args:
            task: Объект задания
            user_input: Ответ пользователя
        
        Returns:
            Объект CheckResponse с результатом
        """
        # Форматирование ответа
        answer_str = self.format_answer_for_check(task, user_input)
        
        # Подготовка данных для отправки
        data = {
            'guid': task.guid,
            'answer': answer_str,
            'ajax': '1',
            'proj': self.project_id
        }
        
        # Отправка запроса
        url = f"{BASE_URL}{SOLVE_ENDPOINT}"
        
        try:
            response = self.session.post(
                url,
                data=data,
                timeout=REQUEST_TIMEOUT,
                verify=False
            )
            response.raise_for_status()
            
            # Задержка между запросами
            time.sleep(REQUEST_DELAY)
            
            # Обработка ответа
            result_code = response.text.strip()
            result = self._parse_result_code(result_code)
            
            return CheckResponse(
                guid=task.guid,
                result=result,
                user_answer=answer_str
            )
        
        except requests.RequestException as e:
            print(f"Ошибка при проверке ответа: {e}")
            return CheckResponse(
                guid=task.guid,
                result=CheckResult.ERROR,
                user_answer=answer_str
            )
    
    def _parse_result_code(self, code: str) -> CheckResult:
        """
        Преобразовать код ответа в CheckResult
        
        Args:
            code: Код от сервера ('1', '2', '3', '0')
        
        Returns:
            CheckResult
        """
        result_str = RESULT_CODES.get(code, 'error')
        
        if result_str == 'correct':
            return CheckResult.CORRECT
        elif result_str == 'incorrect':
            return CheckResult.INCORRECT
        elif result_str == 'partially_correct':
            return CheckResult.PARTIALLY_CORRECT
        else:
            return CheckResult.ERROR
    
    def batch_check(self, checks: list) -> list:
        """
        Проверить несколько заданий
        
        Args:
            checks: Список кортежей (task, user_input)
        
        Returns:
            Список CheckResponse
        """
        results = []
        
        for idx, (task, user_input) in enumerate(checks, 1):
            print(f"[{idx}/{len(checks)}] Проверка задания {task.task_id}...")
            result = self.check_answer(task, user_input)
            results.append(result)
            
            print(f"  Результат: {result.result.value}")
        
        return results


class AnswerHelper:
    """Вспомогательные методы для работы с ответами"""
    
    @staticmethod
    def binary_string_to_indices(binary_str: str) -> list:
        """
        Преобразовать бинарную строку в список индексов
        
        Args:
            binary_str: Строка типа "10100"
        
        Returns:
            [0, 2] - индексы выбранных вариантов
        """
        return [i for i, bit in enumerate(binary_str) if bit == '1']
    
    @staticmethod
    def indices_to_binary_string(indices: list, total: int) -> str:
        """
        Преобразовать список индексов в бинарную строку
        
        Args:
            indices: [0, 2]
            total: Всего вариантов (например, 5)
        
        Returns:
            "10100"
        """
        bits = ['0'] * total
        for idx in indices:
            if 0 <= idx < total:
                bits[idx] = '1'
        return ''.join(bits)
    
    @staticmethod
    def parse_matching_answer(answer_str: str) -> dict:
        """
        Преобразовать строку ответа соответствия в словарь
        
        Args:
            answer_str: "24" (А-2, Б-4)
        
        Returns:
            {"А": "2", "Б": "4"}
        """
        result = {}
        letters = ['А', 'Б', 'В', 'Г', 'Д']
        
        for idx, digit in enumerate(answer_str):
            if idx < len(letters):
                result[letters[idx]] = digit
        
        return result
    
    @staticmethod
    def format_matching_answer(mapping: dict) -> str:
        """
        Преобразовать словарь соответствия в строку
        
        Args:
            mapping: {"А": "2", "Б": "4"}
        
        Returns:
            "24"
        """
        sorted_letters = sorted(mapping.keys())
        return ''.join(str(mapping[letter]) for letter in sorted_letters)


# Пример использования
if __name__ == "__main__":
    from parser import FIPIParser
    from utils import FileManager
    
    # Загрузка сохранённого задания
    fm = FileManager()
    
    # Находим задания по физике
    physics_dirs = fm.find_tasks_by_subject('physics')
    
    if physics_dirs:
        # Берём первое задание
        task_dir = physics_dirs[0]
        task = fm.load_task(task_dir)
        
        if task:
            print(f"Загружено задание: {task.task_id}")
            print(f"Тип: {task.task_type.value}")
            print(f"Вопрос: {task.question_text[:100]}...")
            
            # Создаём checker
            checker = FIPIChecker('physics')
            
            # Пример проверки (нужно подставить реальный ответ)
            if task.task_type == TaskType.SHORT_ANSWER:
                user_answer = "35"  # Пример ответа
                result = checker.check_answer(task, user_answer)
                print(f"\nРезультат проверки: {result.result.value}")
            
            elif task.task_type == TaskType.MULTIPLE_CHOICE:
                user_answer = [0, 2]  # Выбраны 1-й и 3-й варианты
                result = checker.check_answer(task, user_answer)
                print(f"\nРезультат проверки: {result.result.value}")
            
            elif task.task_type == TaskType.MATCHING:
                user_answer = {"А": "2", "Б": "4"}
                result = checker.check_answer(task, user_answer)
                print(f"\nРезультат проверки: {result.result.value}")
    else:
        print("Нет сохранённых заданий. Сначала запустите parser.py")

