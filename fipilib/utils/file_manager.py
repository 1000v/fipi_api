"""
Менеджер для сохранения и загрузки заданий
"""
import os
import json
from pathlib import Path
from typing import Optional, List, Dict
import requests

from ..models.task import Task


class FileManager:
    """Менеджер для работы с файлами заданий"""
    
    def __init__(self, base_dir: str = "data"):
        """
        Args:
            base_dir: Базовая директория для хранения данных
        """
        self.base_dir = Path(base_dir)
    
    def get_task_directory(self, task: Task) -> Path:
        """
        Получить директорию для задания
        Структура: data/{предмет}/{КЭС}/{GUID}/
        
        Args:
            task: Задание
        
        Returns:
            Path к директории
        """
        subject_dir = self.base_dir / task.subject
        
        # Определяем папку по КЭС
        if task.kes_codes:
            kes_code = task.kes_codes[0]
            kes_number = kes_code.split()[0] if ' ' in kes_code else kes_code
            kes_folder = kes_number.replace('.', '_')
            kes_dir = subject_dir / kes_folder
        else:
            kes_dir = subject_dir / "unknown_kes"
        
        task_dir = kes_dir / task.guid
        return task_dir
    
    def save_task(self, task: Task) -> Dict[str, str]:
        """
        Сохранить задание в JSON и Markdown
        
        Args:
            task: Задание для сохранения
        
        Returns:
            Dict с путями к созданным файлам
        """
        task_dir = self.get_task_directory(task)
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохранение JSON
        json_path = task_dir / "task.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(task.to_json())
        
        # Сохранение Markdown
        md_path = task_dir / "task.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self._task_to_markdown(task))
        
        return {
            'json': str(json_path),
            'markdown': str(md_path),
            'directory': str(task_dir)
        }
    
    def load_task(self, task_dir: Path) -> Optional[Task]:
        """
        Загрузить задание из директории
        
        Args:
            task_dir: Путь к директории задания
        
        Returns:
            Task или None
        """
        json_path = task_dir / "task.json"
        
        if not json_path.exists():
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Task.from_dict(data)
    
    def find_tasks_by_subject(self, subject: str) -> List[Path]:
        """
        Найти все задания по предмету
        
        Args:
            subject: Ключ предмета
        
        Returns:
            Список путей к директориям заданий
        """
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
    
    def get_statistics(self, subject: Optional[str] = None) -> Dict:
        """
        Получить статистику по сохранённым заданиям
        
        Args:
            subject: Предмет (None = все предметы)
        
        Returns:
            Dict со статистикой
        """
        stats = {
            'total_tasks': 0,
            'by_subject': {},
            'by_kes': {}
        }
        
        if not self.base_dir.exists():
            return stats
        
        subjects = [subject] if subject else [
            d.name for d in self.base_dir.iterdir() if d.is_dir()
        ]
        
        for subj in subjects:
            subject_dir = self.base_dir / subj
            if not subject_dir.exists():
                continue
            
            task_count = 0
            kes_counts = {}
            
            for kes_dir in subject_dir.iterdir():
                if kes_dir.is_dir():
                    kes_name = kes_dir.name
                    kes_task_count = sum(
                        1 for td in kes_dir.iterdir()
                        if td.is_dir() and (td / "task.json").exists()
                    )
                    task_count += kes_task_count
                    kes_counts[kes_name] = kes_task_count
            
            stats['by_subject'][subj] = task_count
            stats['by_kes'][subj] = kes_counts
            stats['total_tasks'] += task_count
        
        return stats
    
    def _task_to_markdown(self, task: Task) -> str:
        """Конвертировать задание в Markdown"""
        lines = []
        lines.append(f"# Задание {task.task_id}")
        lines.append(f"\n**GUID:** `{task.guid}`")
        lines.append(f"\n**Предмет:** {task.subject}")
        lines.append(f"\n**Тип:** {task.task_type.value}")
        
        if task.kes_codes:
            lines.append(f"\n**КЭС:** {', '.join(task.kes_codes)}")
        
        lines.append("\n## Текст задания\n")
        lines.append(task.question_text)
        
        if task.images:
            lines.append("\n## Изображения\n")
            for img in task.images:
                lines.append(f"- `{img}`")
        
        if task.metadata:
            lines.append("\n## Метаданные\n")
            for key, value in task.metadata.items():
                lines.append(f"- **{key}:** {value}")
        
        return "\n".join(lines)

