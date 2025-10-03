"""
Конфигурация предметов
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class SubjectConfig:
    """Конфигурация для конкретного предмета"""
    subject_key: str  # Ключ предмета (physics, math_prof и т.д.)
    project_id: str  # ID проекта в системе ФИПИ
    display_name: str  # Отображаемое имя
    base_url: str = "https://ege.fipi.ru"
    request_timeout: int = 30
    request_delay: float = 1.0


# Доступные предметы
SUBJECTS: Dict[str, SubjectConfig] = {
    "physics": SubjectConfig(
        subject_key="physics",
        project_id="BA1F39653304A5B041B656915DC36B38",
        display_name="Физика"
    ),
    "math_prof": SubjectConfig(
        subject_key="math_prof",
        project_id="AC437B34557F88EA4115D2F374B0A07B",
        display_name="Математика (профильный уровень)"
    ),
    "russian": SubjectConfig(
        subject_key="russian",
        project_id="CA9D848CF10554A28617021C9211069B",
        display_name="Русский язык"
    ),
}


def get_subject_config(subject_key: str) -> SubjectConfig:
    """
    Получить конфигурацию предмета
    
    Args:
        subject_key: Ключ предмета
    
    Returns:
        SubjectConfig
    
    Raises:
        ValueError: Если предмет не найден
    """
    if subject_key not in SUBJECTS:
        available = ', '.join(SUBJECTS.keys())
        raise ValueError(
            f"Предмет '{subject_key}' не найден. "
            f"Доступные предметы: {available}"
        )
    
    return SUBJECTS[subject_key]

