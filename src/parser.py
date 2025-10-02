"""
Парсер заданий с сайта ФИПИ
"""
import re
import time
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
import requests
import urllib3

# Отключение предупреждений о SSL (для обхода проблем с сертификатом ФИПИ)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .config import (
    BASE_URL, QUESTIONS_ENDPOINT, SUBJECTS, 
    DEFAULT_PAGE_SIZE, REQUEST_TIMEOUT, REQUEST_DELAY, HEADERS
)
from .models import Task, TaskType, AnswerVariant, MatchingOption, MatchingChoice
from .utils import FileManager, extract_image_urls_from_html, clean_text


class FIPIParser:
    """Парсер заданий ФИПИ"""
    
    def __init__(self, subject_key: str):
        """
        Инициализация парсера
        
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
        
        self.file_manager = FileManager()
    
    def get_questions_page(self, page: int = 0, page_size: int = DEFAULT_PAGE_SIZE) -> str:
        """
        Получить HTML страницу с заданиями
        
        Args:
            page: Номер страницы (начиная с 0)
            page_size: Количество заданий на странице
        
        Returns:
            HTML контент страницы
        """
        url = f"{BASE_URL}{QUESTIONS_ENDPOINT}"
        params = {
            'proj': self.project_id,
            'page': page,
            'pagesize': page_size
        }
        
        try:
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            time.sleep(REQUEST_DELAY)  # Задержка между запросами
            return response.text
        except requests.RequestException as e:
            print(f"Ошибка при получении страницы {page}: {e}")
            return ""
    
    def parse_task_from_block(self, block: BeautifulSoup) -> Optional[Task]:
        """
        Распарсить одно задание из блока div.qblock
        
        Args:
            block: BeautifulSoup объект блока задания
        
        Returns:
            Объект Task или None если парсинг не удался
        """
        try:
            # Извлечение GUID
            guid_input = block.find('input', {'name': 'guid'})
            if not guid_input:
                return None
            guid = guid_input.get('value', '')
            
            # Извлечение публичного номера
            task_id_span = block.find('span', class_='canselect')
            task_id = task_id_span.get_text(strip=True) if task_id_span else guid[:8]
            
            # Извлечение текста задания
            cell0 = block.find('td', class_='cell_0')
            if not cell0:
                return None
            
            question_html = str(cell0)
            question_text = clean_text(cell0.get_text())
            
            # Извлечение изображений
            images = extract_image_urls_from_html(question_html)
            
            # Извлечение КЭС из task-info-panel
            kes_codes = self._parse_kes_from_block(block)
            
            # Определение типа задания и парсинг блока ответов
            variants_block = block.find('div', class_='varinats-block')
            if not variants_block:
                variants_block = block
            
            task_type, answer_data = self._parse_answer_block(variants_block)
            
            # Создание объекта задания
            task = Task(
                guid=guid,
                task_id=task_id,
                subject=self.subject_name,
                task_type=task_type,
                question_text=question_text,
                question_html=question_html,
                images=images,
                kes_codes=kes_codes,
                **answer_data
            )
            
            return task
        
        except Exception as e:
            print(f"Ошибка при парсинге блока задания: {e}")
            return None
    
    def _parse_kes_from_block(self, block: BeautifulSoup) -> List[str]:
        """
        Извлечь коды КЭС из блока задания
        
        ЛОГИКА:
        - Блок задания: <div class="qblock" id="q474F4B">
        - Блок с инфо: <div id="i474F4B"> (i + ID задания)
        
        Args:
            block: BeautifulSoup объект блока задания
        
        Returns:
            Список кодов КЭС (например, ["2.2 Иррациональные уравнения"])
        """
        kes_codes = []
        
        try:
            # Получаем ID задания из qblock
            # Формат: id="q474F4B" -> нужно "474F4B"
            qblock_id = block.get('id', '')
            if not qblock_id or not qblock_id.startswith('q'):
                return kes_codes
            
            # Убираем префикс 'q' для получения чистого ID
            task_id = qblock_id[1:]  # "q474F4B" -> "474F4B"
            
            # Ищем соответствующий div с информацией: id="i474F4B"
            info_block_id = f'i{task_id}'
            
            # Получаем корневой soup для поиска
            soup = block.find_parent() or block
            while soup.parent:
                soup = soup.parent
            
            # Ищем блок с информацией по ID
            info_block = soup.find('div', id=info_block_id)
            
            if not info_block:
                return kes_codes
            
            # Внутри ищем task-info-panel
            info_panel = info_block.find('div', class_='task-info-panel')
            
            if not info_panel:
                return kes_codes
            
            # Ищем таблицу с параметрами
            info_table = info_panel.find('table')
            if not info_table:
                return kes_codes
            
            # Ищем строку с КЭС
            rows = info_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    param_name = cells[0].get_text(strip=True)
                    if 'КЭС' in param_name or 'кэс' in param_name.lower():
                        # Извлекаем значение КЭС
                        param_row = cells[1]
                        # Может быть несколько div'ов с разными КЭС
                        kes_divs = param_row.find_all('div')
                        if kes_divs:
                            for kes_div in kes_divs:
                                kes_text = clean_text(kes_div.get_text())
                                if kes_text:
                                    kes_codes.append(kes_text)
                        else:
                            # Если нет div, берём весь текст
                            kes_text = clean_text(param_row.get_text())
                            if kes_text:
                                kes_codes.append(kes_text)
        
        except Exception as e:
            print(f"  Ошибка при парсинге КЭС: {e}")
        
        return kes_codes
    
    def _parse_answer_block(self, block: BeautifulSoup) -> tuple:
        """
        Определить тип задания и извлечь данные блока ответа
        
        Returns:
            (TaskType, dict с данными для конструктора Task)
        """
        # Проверка на краткий ответ
        text_input = block.find('input', {'type': 'text', 'name': 'answer'})
        if text_input:
            # Попытка найти единицу измерения
            answer_unit = None
            parent = text_input.parent
            if parent:
                text_after = parent.get_text()
                # Ищем текст после поля ввода
                match = re.search(r'</input>\s*([а-яА-Яa-zA-Z°]+)', str(parent))
                if match:
                    answer_unit = match.group(1).strip()
            
            return TaskType.SHORT_ANSWER, {'answer_unit': answer_unit}
        
        # Проверка на множественный выбор (checkbox)
        checkboxes = block.find_all('input', {'type': 'checkbox'})
        if checkboxes:
            variants = []
            active_rows = block.find_all('tr', class_='active-distractor')
            
            for idx, row in enumerate(active_rows):
                checkbox = row.find('input', {'type': 'checkbox'})
                if not checkbox:
                    continue
                
                # Текст варианта в последней td
                text_cell = row.find_all('td')[-1]
                variant_text = clean_text(text_cell.get_text()) if text_cell else ""
                
                input_name = checkbox.get('name', f'test{idx}')
                
                variants.append(AnswerVariant(
                    index=idx,
                    text=variant_text,
                    input_name=input_name
                ))
            
            return TaskType.MULTIPLE_CHOICE, {'answer_variants': variants}
        
        # Проверка на установление соответствия (select)
        selects = block.find_all('select')
        if selects:
            options = []
            choices = []
            
            # Парсинг левого столбца (А, Б, ...)
            answer_table = block.find('table', class_='answer-table')
            if answer_table:
                # Ищем все select'ы и соответствующие тексты
                for idx, select in enumerate(selects):
                    select_name = select.get('name', f'ans{idx}')
                    
                    # Попытка найти букву и текст
                    parent_td = select.find_parent('td')
                    if parent_td:
                        # Ищем предыдущий td с буквой
                        prev_td = parent_td.find_previous_sibling('td')
                        if prev_td:
                            letter = clean_text(prev_td.get_text())
                        else:
                            letter = chr(ord('А') + idx)
                        
                        # Ищем текст описания (обычно выше в таблице)
                        # Это упрощённая логика - может потребоваться уточнение
                        text = f"Вариант {letter}"
                        
                        options.append(MatchingOption(
                            letter=letter,
                            text=text,
                            select_name=select_name
                        ))
            
            # Парсинг правого столбца (1, 2, 3, ...)
            # Обычно варианты для выбора находятся в отдельной таблице
            choice_rows = block.find_all('tr')
            for row in choice_rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    # Первая ячейка - номер, вторая - текст
                    number_cell = cells[0]
                    text_cell = cells[1]
                    
                    number_text = clean_text(number_cell.get_text())
                    if re.match(r'^\d+\)', number_text):
                        number = number_text.replace(')', '').strip()
                        choice_text = clean_text(text_cell.get_text())
                        
                        choices.append(MatchingChoice(
                            number=number,
                            text=choice_text
                        ))
            
            return TaskType.MATCHING, {
                'matching_options': options,
                'matching_choices': choices
            }
        
        # По умолчанию - краткий ответ
        return TaskType.SHORT_ANSWER, {}
    
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
            task = self.parse_task_from_block(block)
            if task:
                tasks.append(task)
        
        return tasks
    
    def parse_and_save(self, page: int = 0, page_size: int = DEFAULT_PAGE_SIZE, 
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
        print(f"Получение страницы {page} ({self.subject_info['name']})...")
        html = self.get_questions_page(page, page_size)
        
        if not html:
            print("Не удалось получить страницу")
            return []
        
        print("Парсинг заданий...")
        tasks = self.parse_page(html)
        
        print(f"Найдено заданий: {len(tasks)}")
        
        saved_tasks = []
        for idx, task in enumerate(tasks, 1):
            print(f"[{idx}/{len(tasks)}] Сохранение {task.task_id}...")
            
            # Скачивание изображений
            if download_images and task.images:
                try:
                    downloaded_paths = self.file_manager.download_images(task, self.session)
                    if downloaded_paths:
                        print(f"  Скачано изображений: {len(downloaded_paths)}")
                except Exception as e:
                    print(f"  Ошибка при скачивании изображений: {e}")
            
            # Сохранение задания (пути к изображениям будут обновлены на локальные)
            try:
                paths = self.file_manager.save_task(task, update_image_paths=True)
                print(f"  Сохранено: {paths['directory']}")
                saved_tasks.append(task)
            except Exception as e:
                print(f"  Ошибка при сохранении: {e}")
        
        return saved_tasks
    
    def parse_multiple_pages(self, start_page: int = 0, num_pages: int = 5,
                            page_size: int = DEFAULT_PAGE_SIZE,
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
        """
        Получить общее количество заданий для предмета
        
        Извлекает количество из вызова JavaScript функции setQCount
        
        Returns:
            Количество заданий (0 если не удалось определить)
        """
        try:
            # Получаем первую страницу с заданиями
            html = self.get_questions_page(0, 1)
            
            if not html:
                return 0
            
            # Ищем вызов функции setQCount в JavaScript коде
            # Формат: setQCount(863, 1, 10) или setQCount(863)
            import re
            match = re.search(r'setQCount\s*\(\s*(\d+)', html)
            if match:
                return int(match.group(1))
            
            return 0
        
        except Exception as e:
            print(f"  Ошибка при получении количества заданий: {e}")
            return 0
    
    def parse_all_tasks(self, page_size: int = DEFAULT_PAGE_SIZE, 
                       download_images: bool = True,
                       max_tasks: Optional[int] = None) -> List[Task]:
        """
        Распарсить ВСЕ задания по предмету
        
        Args:
            page_size: Количество заданий на странице
            download_images: Скачивать ли изображения
            max_tasks: Максимальное количество заданий (None = все)
        
        Returns:
            Список всех сохранённых заданий
        """
        print("=" * 60)
        print(f"МАСШТАБНЫЙ ПАРСИНГ: {self.subject_info['name']}")
        print("=" * 60)
        
        # Получаем общее количество заданий
        print("\nОпределение количества заданий...")
        total_count = self.get_total_tasks_count()
        
        if total_count > 0:
            print(f"[OK] Всего заданий в базе ФИПИ: {total_count}")
            
            if max_tasks:
                actual_limit = min(total_count, max_tasks)
                print(f"Лимит для парсинга: {max_tasks}")
                print(f"Будет спарсено: {actual_limit} заданий")
                print(f"Ориентировочно страниц: ~{(actual_limit + page_size - 1) // page_size}")
            else:
                print(f"Режим: Парсинг всех {total_count} заданий")
                print(f"Ориентировочно страниц: ~{(total_count + page_size - 1) // page_size}")
        else:
            print("! Не удалось определить количество заданий")
            
            if max_tasks:
                print(f"Лимит заданий: {max_tasks}")
                print(f"Ориентировочно страниц: ~{(max_tasks + page_size - 1) // page_size}")
            else:
                print("Режим: Парсинг до пустых страниц")
        
        print(f"Размер страницы: {page_size}")
        print(f"Скачивание изображений: {'Да' if download_images else 'Нет'}")
        print("\n" + "=" * 60)
        
        all_tasks = []
        page = 0
        empty_pages = 0
        max_empty_pages = 3  # Остановка после 3 пустых страниц подряд
        
        while True:
            # Проверка лимита
            if max_tasks and len(all_tasks) >= max_tasks:
                print(f"\nДостигнут лимит заданий: {max_tasks}")
                break
            
            # Прогресс
            if max_tasks:
                progress = min(100, (len(all_tasks) / max_tasks) * 100)
                print(f"\n[Страница {page}] Прогресс: {len(all_tasks)}/{max_tasks} ({progress:.1f}%)")
            elif total_count > 0:
                progress = min(100, (len(all_tasks) / total_count) * 100)
                print(f"\n[Страница {page}] Прогресс: {len(all_tasks)}/{total_count} ({progress:.1f}%)")
            else:
                print(f"\n[Страница {page}] Спарсено: {len(all_tasks)} заданий")
            
            # Парсинг страницы
            tasks = self.parse_and_save(page, page_size, download_images)
            
            if tasks:
                all_tasks.extend(tasks)
                empty_pages = 0
            else:
                empty_pages += 1
                print(f"Пустая страница ({empty_pages}/{max_empty_pages})")
                
                if empty_pages >= max_empty_pages:
                    print(f"\nПолучено {max_empty_pages} пустых страниц подряд. Парсинг завершён.")
                    break
            
            page += 1
            
            # Дополнительная проверка на всякий случай
            if page > 1000:
                print("\nДостигнут лимит страниц (1000). Парсинг остановлен.")
                break
        
        print("\n" + "=" * 60)
        print(f"ПАРСИНГ ЗАВЕРШЁН")
        print(f"Всего спарсено и сохранено: {len(all_tasks)} заданий")
        print("=" * 60)
        
        # Статистика
        self._print_parsing_stats(all_tasks)
        
        return all_tasks
    
    def _print_parsing_stats(self, tasks: List[Task]):
        """Вывести статистику по спарсенным заданиям"""
        if not tasks:
            return
        
        from collections import Counter
        
        # Статистика по типам заданий
        type_counts = Counter(task.task_type.value for task in tasks)
        
        print(f"\nСтатистика по типам заданий:")
        for task_type, count in type_counts.items():
            print(f"  - {task_type}: {count}")
        
        # Статистика по КЭС
        kes_counts = Counter()
        for task in tasks:
            if task.kes_codes:
                # Берём первый КЭС код
                kes_code = task.kes_codes[0].split()[0] if ' ' in task.kes_codes[0] else task.kes_codes[0]
                kes_counts[kes_code] += 1
        
        if kes_counts:
            print(f"\nТоп-10 КЭС кодов:")
            for kes, count in kes_counts.most_common(10):
                print(f"  - {kes}: {count} заданий")
        
        # Статистика по изображениям
        tasks_with_images = sum(1 for task in tasks if task.images)
        print(f"\nЗаданий с изображениями: {tasks_with_images}/{len(tasks)}")


# Пример использования
if __name__ == "__main__":
    # Парсинг физики
    physics_parser = FIPIParser('physics')
    physics_tasks = physics_parser.parse_and_save(page=0, page_size=5)
    
    # Парсинг математики
    # math_parser = FIPIParser('math_prof')
    # math_tasks = math_parser.parse_and_save(page=0, page_size=5)
    
    # Статистика
    fm = FileManager()
    stats = fm.get_statistics()
    print("\nСтатистика:")
    print(f"Всего заданий: {stats['total_tasks']}")
    print(f"По предметам: {stats['by_subject']}")

