"""
Базовый абстрактный класс для парсеров заданий
Каждый предмет может переопределить специфичные методы
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
import time

from ..models.task import Task, TaskType
from ..models.config import SubjectConfig
from .session_manager import SessionManager


class BaseParser(ABC):
    """
    Абстрактный базовый парсер для всех предметов
    
    Реализует общую логику получения страниц и базовый парсинг
    Предметы могут переопределить специфичные методы
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
    
    def get_questions_page(self, page: int = 0, page_size: int = 10) -> str:
        """
        Получить HTML страницу с заданиями
        
        Args:
            page: Номер страницы (начиная с 0)
            page_size: Количество заданий на странице
        
        Returns:
            HTML контент страницы
        """
        url = f"{self.config.base_url}/bank/questions.php"
        params = {
            'proj': self.config.project_id,
            'page': page,
            'pagesize': page_size
        }
        
        try:
            response = self.session.get(
                url, 
                params=params, 
                timeout=self.config.request_timeout,
                verify=False
            )
            response.raise_for_status()
            time.sleep(self.config.request_delay)
            return response.text
        except Exception as e:
            print(f"Ошибка при получении страницы {page}: {e}")
            return ""
    
    def parse_page(self, html: str) -> List[Task]:
        """
        Распарсить все задания со страницы
        
        Args:
            html: HTML контент страницы
        
        Returns:
            Список объектов Task
        """
        soup = BeautifulSoup(html, 'html.parser')
        task_blocks = soup.find_all('div', class_='qblock')
        
        tasks = []
        for block in task_blocks:
            task = self.parse_task_block(block)
            if task:
                tasks.append(task)
        
        return tasks
    
    def parse_task_block(self, block: BeautifulSoup) -> Optional[Task]:
        """
        Распарсить один блок задания
        
        Args:
            block: BeautifulSoup объект блока задания
        
        Returns:
            Объект Task или None
        """
        try:
            # Базовая информация (одинаково для всех предметов)
            guid = self._extract_guid(block)
            task_id = self._extract_task_id(block)
            
            if not guid or not task_id:
                return None
            
            # Текст задания
            question_html, question_text = self._extract_question(block)
            
            # Изображения
            images = self._extract_images(question_html)
            
            # КЭС коды
            kes_codes = self._extract_kes(block)
            
            # Тип задания и ответы (специфично для предмета)
            task_type, answer_data = self.parse_answer_block(block)
            
            # Создание задания
            task = Task(
                guid=guid,
                task_id=task_id,
                subject=self.config.subject_key,
                task_type=task_type,
                question_text=question_text,
                question_html=question_html,
                images=images,
                kes_codes=kes_codes,
                **answer_data
            )
            
            # Применяем специфичную обработку предмета
            task = self.post_process_task(task)
            
            return task
        
        except Exception as e:
            print(f"Ошибка при парсинге блока: {e}")
            return None
    
    @abstractmethod
    def parse_answer_block(self, block: BeautifulSoup) -> tuple:
        """
        Парсинг блока ответов (специфично для предмета)
        
        Args:
            block: BeautifulSoup объект блока задания
        
        Returns:
            (TaskType, dict с данными ответов)
        """
        pass
    
    def post_process_task(self, task: Task) -> Task:
        """
        Пост-обработка задания (может быть переопределено в предмете)
        
        Args:
            task: Задание для обработки
        
        Returns:
            Обработанное задание
        """
        return task
    
    def _extract_guid(self, block: BeautifulSoup) -> Optional[str]:
        """Извлечь GUID задания"""
        guid_input = block.find('input', {'name': 'guid'})
        return guid_input.get('value', '') if guid_input else None
    
    def _extract_task_id(self, block: BeautifulSoup) -> Optional[str]:
        """Извлечь публичный ID задания"""
        task_id_span = block.find('span', class_='canselect')
        if task_id_span:
            return task_id_span.get_text(strip=True)
        
        # Fallback - первые 8 символов GUID
        guid_input = block.find('input', {'name': 'guid'})
        if guid_input:
            guid = guid_input.get('value', '')
            return guid[:8] if guid else None
        
        return None
    
    def _extract_question(self, block: BeautifulSoup) -> tuple:
        """Извлечь текст и HTML вопроса"""
        cell0 = block.find('td', class_='cell_0')
        if not cell0:
            return "", ""
        
        question_html = str(cell0)
        question_text = self._clean_text(cell0.get_text())
        
        return question_html, question_text
    
    def _extract_images(self, html: str) -> List[str]:
        """Извлечь URL изображений из HTML"""
        import re
        urls = []
        
        # ShowPictureQ('...')
        show_picture_pattern = r"ShowPictureQ\(['\"]([^'\"]+)['\"]\)"
        matches = re.findall(show_picture_pattern, html)
        urls.extend(matches)
        
        # <img src="...">
        img_src_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        matches = re.findall(img_src_pattern, html)
        urls.extend(matches)
        
        return urls
    
    def _extract_kes(self, block: BeautifulSoup) -> List[str]:
        """Извлечь коды КЭС"""
        kes_codes = []
        
        try:
            qblock_id = block.get('id', '')
            if not qblock_id or not qblock_id.startswith('q'):
                return kes_codes
            
            task_id = qblock_id[1:]
            info_block_id = f'i{task_id}'
            
            # Получаем корневой soup
            soup = block.find_parent() or block
            while soup.parent:
                soup = soup.parent
            
            info_block = soup.find('div', id=info_block_id)
            if not info_block:
                return kes_codes
            
            info_panel = info_block.find('div', class_='task-info-panel')
            if not info_panel:
                return kes_codes
            
            info_table = info_panel.find('table')
            if not info_table:
                return kes_codes
            
            rows = info_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    param_name = cells[0].get_text(strip=True)
                    if 'КЭС' in param_name or 'кэс' in param_name.lower():
                        param_row = cells[1]
                        kes_divs = param_row.find_all('div')
                        if kes_divs:
                            for kes_div in kes_divs:
                                kes_text = self._clean_text(kes_div.get_text())
                                if kes_text:
                                    kes_codes.append(kes_text)
                        else:
                            kes_text = self._clean_text(param_row.get_text())
                            if kes_text:
                                kes_codes.append(kes_text)
        
        except Exception as e:
            print(f"  Ошибка при извлечении КЭС: {e}")
        
        return kes_codes
    
    def _clean_text(self, text: str) -> str:
        """Очистить текст от лишних символов"""
        import re
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        text = text.replace('&nbsp;', ' ')
        return text
    
    def parse_and_save(self, page: int = 0, page_size: int = 10, 
                      download_images: bool = True) -> List[Task]:
        """
        Получить, распарсить и сохранить задания со страницы
        
        Args:
            page: Номер страницы
            page_size: Размер страницы
            download_images: Скачивать ли изображения
        
        Returns:
            Список сохранённых заданий
        """
        from ..utils import FileManager
        
        print(f"Получение страницы {page} ({self.config.display_name})...")
        html = self.get_questions_page(page, page_size)
        
        if not html:
            print("Не удалось получить страницу")
            return []
        
        print("Парсинг заданий...")
        tasks = self.parse_page(html)
        
        print(f"Найдено заданий: {len(tasks)}")
        
        # Сохранение заданий
        file_manager = FileManager()
        saved_tasks = []
        
        for idx, task in enumerate(tasks, 1):
            print(f"[{idx}/{len(tasks)}] Сохранение {task.task_id}...")
            
            # Скачивание изображений
            if download_images and task.images:
                try:
                    downloaded_paths = self._download_images(task)
                    if downloaded_paths:
                        # Обновляем пути на локальные
                        task.images = [f"media/{p.split('/')[-1]}" for p in downloaded_paths]
                        print(f"  Скачано изображений: {len(downloaded_paths)}")
                except Exception as e:
                    print(f"  Ошибка при скачивании изображений: {e}")
            
            # Сохранение задания
            try:
                paths = file_manager.save_task(task)
                print(f"  Сохранено: {paths['directory']}")
                saved_tasks.append(task)
            except Exception as e:
                print(f"  Ошибка при сохранении: {e}")
        
        return saved_tasks
    
    def _download_images(self, task: Task) -> List[str]:
        """
        Скачать изображения для задания
        
        Args:
            task: Задание с изображениями
        
        Returns:
            Список путей к скачанным файлам
        """
        from ..utils import FileManager
        from pathlib import Path
        
        file_manager = FileManager()
        task_dir = file_manager.get_task_directory(task)
        media_dir = task_dir / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        
        for img_url in task.images:
            try:
                # Добавить базовый URL если нужно
                if not img_url.startswith('http'):
                    if not img_url.startswith('/'):
                        img_url = '/' + img_url
                    img_url = self.config.base_url + img_url
                
                response = self.session.get(img_url, timeout=30, verify=False)
                response.raise_for_status()
                
                # Имя файла из URL
                filename = img_url.split('/')[-1]
                if not filename or '?' in filename:
                    filename = f"image_{len(saved_paths)}.png"
                
                image_path = media_dir / filename
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                saved_paths.append(str(image_path))
            except Exception as e:
                print(f"  Ошибка при скачивании {img_url}: {e}")
        
        return saved_paths
    
    def parse_multiple_pages(self, start_page: int = 0, num_pages: int = 5,
                            page_size: int = 10,
                            download_images: bool = True) -> List[Task]:
        """
        Распарсить несколько страниц подряд
        
        Args:
            start_page: Начальная страница
            num_pages: Количество страниц
            page_size: Размер страницы
            download_images: Скачивать ли изображения
        
        Returns:
            Список всех сохранённых заданий
        """
        all_tasks = []
        
        for page in range(start_page, start_page + num_pages):
            tasks = self.parse_and_save(page, page_size, download_images)
            all_tasks.extend(tasks)
            
            if not tasks:
                print(f"Страница {page} пуста, прекращаем парсинг")
                break
        
        print(f"\nВсего сохранено заданий: {len(all_tasks)}")
        return all_tasks
    
    def get_total_tasks_count(self) -> int:
        """Получить общее количество заданий"""
        try:
            html = self.get_questions_page(0, 1)
            if not html:
                return 0
            
            import re
            match = re.search(r'setQCount\s*\(\s*(\d+)', html)
            if match:
                return int(match.group(1))
            
            return 0
        except Exception as e:
            print(f"Ошибка при получении количества заданий: {e}")
            return 0

