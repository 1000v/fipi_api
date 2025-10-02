"""
Утилиты для работы с файлами и данными
"""
import os
import json
import re
from pathlib import Path
from typing import Optional, List
import requests
from .models import Task
from .config import DATA_DIR


class FileManager:
    """Менеджер для сохранения и загрузки заданий"""
    
    def __init__(self, base_dir: str = DATA_DIR):
        self.base_dir = Path(base_dir)
    
    def get_task_directory(self, task: Task) -> Path:
        """
        Получить директорию для сохранения задания
        Структура: data/{предмет}/{КЭС}/{GUID}/
        """
        subject_dir = self.base_dir / task.subject
        
        # Если есть коды КЭС, создаём папки для них
        if task.kes_codes:
            # Берём первый КЭС код и извлекаем только код (например "2.2" из "2.2 Иррациональные уравнения")
            kes_code = task.kes_codes[0]
            # Извлекаем числовой код (до первого пробела)
            kes_number = kes_code.split()[0] if ' ' in kes_code else kes_code
            # Заменяем точки на подчёркивания для имени папки
            kes_folder = kes_number.replace('.', '_')
            kes_dir = subject_dir / kes_folder
        else:
            kes_dir = subject_dir / "unknown_kes"
        
        task_dir = kes_dir / task.guid
        return task_dir
    
    def save_task(self, task: Task, update_image_paths: bool = True) -> dict:
        """
        Сохранить задание в JSON и Markdown
        
        Args:
            task: Задание для сохранения
            update_image_paths: Обновить пути изображений на локальные (по умолчанию True)
        
        Возвращает пути к созданным файлам
        """
        task_dir = self.get_task_directory(task)
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Если нужно обновить пути к изображениям
        if update_image_paths and task.images:
            # Сохраняем оригинальные URL в метаданные
            if 'original_image_urls' not in task.metadata:
                task.metadata['original_image_urls'] = task.images.copy()
            
            # Обновляем пути на локальные
            local_image_paths = []
            media_dir = task_dir / "media"
            
            if media_dir.exists():
                # Находим все скачанные изображения
                for img_file in media_dir.iterdir():
                    if img_file.is_file():
                        # Относительный путь от директории задания
                        rel_path = f"media/{img_file.name}"
                        local_image_paths.append(rel_path)
            
            # Если изображения были скачаны, обновляем список
            if local_image_paths:
                task.images = local_image_paths
        
        # Сохранение JSON
        json_path = task_dir / "task.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(task.to_json())
        
        # Сохранение Markdown
        md_path = task_dir / "task.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(task.to_markdown())
        
        return {
            'json': str(json_path),
            'markdown': str(md_path),
            'directory': str(task_dir)
        }
    
    def load_task(self, task_dir: Path) -> Optional[Task]:
        """Загрузить задание из директории"""
        json_path = task_dir / "task.json"
        
        if not json_path.exists():
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Task.from_dict(data)
    
    def save_image(self, task: Task, image_url: str, image_data: bytes) -> str:
        """
        Сохранить изображение в директорию задания
        Возвращает путь к сохранённому файлу
        """
        task_dir = self.get_task_directory(task)
        media_dir = task_dir / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        
        # Извлечь имя файла из URL
        filename = os.path.basename(image_url)
        if not filename:
            filename = f"image_{len(os.listdir(media_dir))}.png"
        
        image_path = media_dir / filename
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        return str(image_path)
    
    def download_images(self, task: Task, session: requests.Session) -> List[str]:
        """
        Скачать все изображения для задания
        Возвращает список путей к сохранённым файлам
        """
        saved_paths = []
        
        for img_url in task.images:
            try:
                # Добавить базовый URL если нужно
                if not img_url.startswith('http'):
                    from config import BASE_URL
                    # Добавляем слеш если его нет
                    if not img_url.startswith('/'):
                        img_url = '/' + img_url
                    img_url = BASE_URL + img_url
                
                response = session.get(img_url, timeout=30, verify=False)
                response.raise_for_status()
                
                path = self.save_image(task, img_url, response.content)
                saved_paths.append(path)
            except Exception as e:
                print(f"Ошибка при скачивании {img_url}: {e}")
        
        return saved_paths
    
    def find_tasks_by_subject(self, subject: str) -> List[Path]:
        """Найти все задания по предмету"""
        # Проверяем существование базовой директории
        if not self.base_dir.exists():
            return []
        
        subject_dir = self.base_dir / subject
        
        if not subject_dir.exists():
            return []
        
        task_dirs = []
        for kes_dir in subject_dir.iterdir():
            if kes_dir.is_dir():
                for task_dir in kes_dir.iterdir():
                    if task_dir.is_dir() and (task_dir / "task.json").exists():
                        task_dirs.append(task_dir)
        
        return task_dirs
    
    def get_statistics(self, subject: Optional[str] = None) -> dict:
        """Получить статистику по сохранённым заданиям"""
        stats = {
            'total_tasks': 0,
            'by_subject': {},
            'by_kes': {}
        }
        
        # Проверяем существование базовой директории
        if not self.base_dir.exists():
            return stats
        
        if subject:
            subjects_to_check = [subject]
        else:
            subjects_to_check = [d.name for d in self.base_dir.iterdir() if d.is_dir()]
        
        for subj in subjects_to_check:
            subject_dir = self.base_dir / subj
            if not subject_dir.exists():
                continue
            
            task_count = 0
            kes_counts = {}
            
            for kes_dir in subject_dir.iterdir():
                if kes_dir.is_dir():
                    kes_name = kes_dir.name
                    kes_task_count = sum(1 for td in kes_dir.iterdir() 
                                        if td.is_dir() and (td / "task.json").exists())
                    task_count += kes_task_count
                    kes_counts[kes_name] = kes_task_count
            
            stats['by_subject'][subj] = task_count
            stats['by_kes'][subj] = kes_counts
            stats['total_tasks'] += task_count
        
        return stats


def extract_image_urls_from_html(html: str) -> List[str]:
    """
    Извлечь URL изображений из HTML
    Ищет вызовы ShowPictureQ и src в тегах img
    """
    urls = []
    
    # Паттерн для ShowPictureQ('...')
    show_picture_pattern = r"ShowPictureQ\(['\"]([^'\"]+)['\"]\)"
    matches = re.findall(show_picture_pattern, html)
    urls.extend(matches)
    
    # Паттерн для <img src="...">
    img_src_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    matches = re.findall(img_src_pattern, html)
    urls.extend(matches)
    
    return urls


def clean_text(text: str) -> str:
    """Очистить текст от лишних пробелов и переносов"""
    # Убрать множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    # Убрать пробелы в начале и конце
    text = text.strip()
    # Убрать &nbsp;
    text = text.replace('&nbsp;', ' ')
    return text


def parse_kes_from_metadata(metadata: dict) -> List[str]:
    """
    Извлечь коды КЭС из метаданных
    (В реальности нужно парсить из HTML страницы фильтров)
    """
    # Заглушка - нужно реализовать парсинг КЭС из темы/фильтра
    return []

