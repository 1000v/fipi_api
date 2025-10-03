"""
Менеджер сессий для работы с ФИПИ
Управляет HTTP-сессиями и cookies
"""
import requests
import urllib3
from pathlib import Path
from typing import Dict, Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SessionManager:
    """Менеджер для управления HTTP сессиями"""
    
    def __init__(self, cookie_file: Optional[str] = None, cookies: Optional[Dict[str, str]] = None):
        """
        Args:
            cookie_file: Путь к файлу с cookies (опционально)
            cookies: Словарь с cookies (опционально)
        """
        self.session = requests.Session()
        self.cookie_file = Path(cookie_file) if cookie_file else None
        self.cookies_dict = cookies or {}
        self._setup_session()
    
    def _setup_session(self):
        """Настроить сессию с заголовками"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.session.headers.update(headers)
        self.session.verify = False
        
        # Загружаем cookies из словаря (приоритет)
        if self.cookies_dict:
            self.session.cookies.update(self.cookies_dict)
            print(f"[OK] Загружено {len(self.cookies_dict)} cookies из словаря")
        # Или из файла
        elif self.cookie_file:
            # Поиск файла cookies.txt в разных местах
            cookie_paths = [
                self.cookie_file,
                Path('cookies.txt'),
                Path('fipilib/cookies.txt'),
                Path(__file__).parent.parent / 'cookies.txt'
            ]
            
            for cookie_path in cookie_paths:
                if cookie_path.exists():
                    self.cookie_file = cookie_path
                    self.load_cookies()
                    break
            else:
                print(f"[WARNING] Файл cookies не найден. Проверка ответов может не работать.")
                print(f"[INFO] Создайте файл cookies.txt или передайте cookies в код")
    
    def load_cookies(self) -> Dict[str, str]:
        """Загрузить cookies из файла"""
        if not self.cookie_file or not self.cookie_file.exists():
            return {}
        
        cookies = {}
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        name, value = line.split('=', 1)
                        cookies[name.strip()] = value.strip()
            
            if cookies:
                self.session.cookies.update(cookies)
                print(f"[OK] Загружено {len(cookies)} cookies из {self.cookie_file}")
                
                # Показываем какие cookies загружены
                cookie_names = ', '.join(cookies.keys())
                print(f"[INFO] Cookies: {cookie_names}")
            else:
                print(f"[WARNING] Файл {self.cookie_file} пуст")
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке cookies: {e}")
        
        return cookies
    
    def save_cookies(self):
        """Сохранить текущие cookies в файл"""
        if not self.cookie_file:
            return
        
        with open(self.cookie_file, 'w', encoding='utf-8') as f:
            f.write("# Cookies для FIPI\n")
            f.write("# Автоматически сохранено\n\n")
            for name, value in self.session.cookies.items():
                f.write(f"{name}={value}\n")
        
        print(f"[OK] Cookies сохранены")
    
    def get_session(self) -> requests.Session:
        """Получить настроенную сессию"""
        return self.session

