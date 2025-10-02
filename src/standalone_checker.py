"""
Независимая система проверки ответов ФИПИ
Работает как с локальными заданиями, так и напрямую через GUID
"""
import sys
import io
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
import requests
import urllib3

# Исправление кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Отключение предупреждений SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .config import BASE_URL, SUBJECTS
from .models import Task, TaskType, CheckResult
from .utils import FileManager


class CookieManager:
    """Менеджер для работы с cookies из файла"""
    
    def __init__(self, cookie_file: str = "cookies.txt"):
        self.cookie_file = Path(cookie_file)
        self.cookies = {}
    
    def load_cookies(self) -> Dict[str, str]:
        """Загрузить cookies из файла"""
        if not self.cookie_file.exists():
            print(f"[!] Файл {self.cookie_file} не найден")
            return {}
        
        cookies = {}
        with open(self.cookie_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем комментарии и пустые строки
                if not line or line.startswith('#'):
                    continue
                
                # Формат: name=value
                if '=' in line:
                    name, value = line.split('=', 1)
                    cookies[name.strip()] = value.strip()
        
        if cookies:
            print(f"[OK] Загружено {len(cookies)} cookies из {self.cookie_file}")
        else:
            print(f"[!] Cookies не найдены в {self.cookie_file}")
        
        self.cookies = cookies
        return cookies
    
    def save_cookies(self, cookies: Dict[str, str]):
        """Сохранить cookies в файл"""
        with open(self.cookie_file, 'w', encoding='utf-8') as f:
            f.write("# Cookies для FIPI\n")
            f.write("# Автоматически сохранено\n\n")
            for name, value in cookies.items():
                f.write(f"{name}={value}\n")
        
        print(f"[OK] Cookies сохранены в {self.cookie_file}")


class StandaloneChecker:
    """
    Независимая система проверки ответов
    Может работать как с локальными заданиями, так и напрямую через GUID
    """
    
    def __init__(self, subject_key: str = 'physics', cookie_file: str = "cookies.txt"):
        """
        Args:
            subject_key: Ключ предмета ('physics' или 'math_prof')
            cookie_file: Путь к файлу с cookies
        """
        if subject_key not in SUBJECTS:
            raise ValueError(f"Неизвестный предмет: {subject_key}")
        
        self.subject_info = SUBJECTS[subject_key]
        self.project_id = self.subject_info['id']
        self.subject_name = self.subject_info['name_en']
        
        # Инициализация сессии
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": f"{BASE_URL}/bank/index.php"
        })
        
        # Загрузка cookies
        self.cookie_manager = CookieManager(cookie_file)
        cookies = self.cookie_manager.load_cookies()
        
        if cookies:
            self.session.cookies.update(cookies)
        
        self.file_manager = FileManager()
    
    def check_by_guid(self, guid: str, answer: str, task_type: str = "short_answer") -> Dict[str, Any]:
        """
        Проверить ответ напрямую по GUID (без локального задания)
        
        Args:
            guid: GUID задания
            answer: Ответ пользователя (уже отформатированный)
            task_type: Тип задания (для логирования)
        
        Returns:
            Dict с результатом проверки
        """
        url = f"{BASE_URL}/bank/solve.php"
        
        try:
            # Используем multipart/form-data как в оригинале
            boundary = '---------------------------247746999627336697471839302941'
            
            # Формируем тело запроса
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
                self.project_id,
                f'--{boundary}--',
                ''
            ]
            
            body = '\r\n'.join(body_parts)
            
            # Заголовки для POST запроса
            headers = {
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'Referer': f'{BASE_URL}/bank/questions.php?proj={self.project_id}&init_filter_themes=1'
            }
            
            # Отправляем запрос
            response = self.session.post(
                url,
                data=body.encode('utf-8'),
                headers=headers,
                timeout=30,
                verify=False
            )
            
            if response.status_code != 200:
                return {
                    'guid': guid,
                    'answer': answer,
                    'result': 'error',
                    'error': f'HTTP {response.status_code}',
                    'task_type': task_type,
                    'success': False
                }
            
            result_code = response.text.strip()
            
            # Преобразуем код в результат
            # Коды: '1', '3' = correct, '2' = incorrect, '0' = error
            result_map = {
                '1': 'correct',
                '3': 'correct',  # Также правильный ответ
                '2': 'incorrect',
                '0': 'error'
            }
            
            result = result_map.get(result_code, 'error')
            
            return {
                'guid': guid,
                'answer': answer,
                'result': result,
                'result_code': result_code,
                'task_type': task_type,
                'success': True
            }
        
        except Exception as e:
            return {
                'guid': guid,
                'answer': answer,
                'result': 'error',
                'error': str(e),
                'task_type': task_type,
                'success': False
            }
    
    def check_task(self, task: Task, user_input: Any) -> Dict[str, Any]:
        """
        Проверить ответ для задания
        
        Args:
            task: Объект задания
            user_input: Ответ пользователя (формат зависит от типа)
        
        Returns:
            Dict с результатом
        """
        # Форматируем ответ
        answer_str = self._format_answer(task, user_input)
        
        # Проверяем
        result = self.check_by_guid(task.guid, answer_str, task.task_type.value)
        result['task_id'] = task.task_id
        
        return result
    
    def check_by_task_id(self, task_id: str, user_input: Any) -> Dict[str, Any]:
        """
        Проверить ответ по ID задания (сначала ищет локально)
        
        Args:
            task_id: Публичный ID задания (например, "0FDA4F")
            user_input: Ответ пользователя
        
        Returns:
            Dict с результатом
        """
        # Пытаемся найти задание локально
        task = self._find_local_task(task_id)
        
        if task:
            print(f"[OK] Задание {task_id} найдено локально")
            return self.check_task(task, user_input)
        else:
            print(f"[!] Задание {task_id} не найдено локально")
            print("[!] Для проверки без локального задания используйте GUID")
            return {
                'task_id': task_id,
                'result': 'error',
                'error': 'Task not found locally. Use GUID instead.',
                'success': False
            }
    
    def _find_local_task(self, task_id: str) -> Optional[Task]:
        """Найти задание в локальной базе"""
        task_dirs = self.file_manager.find_tasks_by_subject(self.subject_name)
        
        for task_dir in task_dirs:
            task = self.file_manager.load_task(task_dir)
            if task and task.task_id == task_id:
                return task
        
        return None
    
    def _format_answer(self, task: Task, user_input: Any) -> str:
        """Форматировать ответ пользователя"""
        if task.task_type == TaskType.SHORT_ANSWER:
            return str(user_input).strip()
        
        elif task.task_type == TaskType.MULTIPLE_CHOICE:
            if isinstance(user_input, str):
                return user_input
            
            # user_input - список индексов
            num_variants = len(task.answer_variants) if task.answer_variants else 5
            answer_bits = ['0'] * num_variants
            
            for idx in user_input:
                if 0 <= idx < num_variants:
                    answer_bits[idx] = '1'
            
            return ''.join(answer_bits)
        
        elif task.task_type == TaskType.MATCHING:
            if isinstance(user_input, str):
                return user_input
            
            if isinstance(user_input, dict):
                sorted_letters = sorted(user_input.keys())
                return ''.join(str(user_input[letter]) for letter in sorted_letters)
            
            elif isinstance(user_input, (list, tuple)):
                return ''.join(str(x) for x in user_input)
        
        return str(user_input)
    
    def test_connection(self) -> bool:
        """Проверить подключение к ФИПИ"""
        try:
            response = self.session.get(
                f"{BASE_URL}/bank/index.php",
                params={'proj': self.project_id},
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                print("[OK] Подключение к ФИПИ успешно")
                return True
            else:
                print(f"[!] Ошибка подключения: HTTP {response.status_code}")
                return False
        
        except Exception as e:
            print(f"[!] Ошибка подключения: {e}")
            return False


def print_result(result: Dict[str, Any]):
    """Красиво вывести результат проверки"""
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТ ПРОВЕРКИ")
    print("=" * 60)
    
    if 'task_id' in result:
        print(f"Задание: {result['task_id']}")
    
    print(f"GUID: {result['guid']}")
    print(f"Ответ: {result['answer']}")
    
    if result.get('task_type'):
        print(f"Тип: {result['task_type']}")
    
    print(f"\nРезультат: {result['result'].upper()}")
    
    symbols = {
        'correct': '✓ ВЕРНО',
        'incorrect': '✗ НЕВЕРНО',
        'partially_correct': '± ЧАСТИЧНО ВЕРНО',
        'error': '! ОШИБКА'
    }
    
    print(f"Статус: {symbols.get(result['result'], '? НЕИЗВЕСТНО')}")
    
    if 'error' in result:
        print(f"Ошибка: {result['error']}")
    
    print("=" * 60)


# Примеры использования
if __name__ == "__main__":
    print("=" * 60)
    print("STANDALONE FIPI CHECKER")
    print("=" * 60)
    
    # Создаём checker
    checker = StandaloneChecker('physics')
    
    # Проверяем подключение
    checker.test_connection()
    
    # ПРИМЕР 1: Проверка по GUID напрямую
    print("\n" + "=" * 60)
    print("ПРИМЕР 1: Проверка по GUID (без локального задания)")
    print("=" * 60)
    
    # Замените на реальный GUID и ответ
    test_guid = "02171933c6b04526b51f2528d71e2cb7"
    test_answer = "10110"  # Бинарная строка для multiple_choice
    
    result = checker.check_by_guid(test_guid, test_answer, "multiple_choice")
    print_result(result)
    
    # ПРИМЕР 2: Проверка локального задания
    print("\n" + "=" * 60)
    print("ПРИМЕР 2: Проверка локального задания")
    print("=" * 60)
    
    result2 = checker.check_by_task_id("0FDA4F", "10110")
    if result2['success']:
        print_result(result2)

