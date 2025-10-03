"""
Стандартный парсер для предметов
"""
import re
from typing import List
from bs4 import BeautifulSoup

from ...core.base_parser import BaseParser
from ...models.task import TaskType, AnswerVariant, MatchingOption, MatchingChoice


class DefaultParser(BaseParser):
    """Стандартная реализация парсера"""
    
    def parse_answer_block(self, block: BeautifulSoup) -> tuple:
        """
        Парсинг блока ответов
        
        Returns:
            (TaskType, dict с данными)
        """
        # Ищем блок с вариантами
        variants_block = block.find('div', class_='varinats-block')
        if not variants_block:
            variants_block = block
        
        # 1. Краткий ответ (text input)
        text_input = variants_block.find('input', {'type': 'text', 'name': 'answer'})
        if text_input:
            return self._parse_short_answer(variants_block)
        
        # 2. Множественный выбор (checkbox)
        checkboxes = variants_block.find_all('input', {'type': 'checkbox'})
        if checkboxes:
            return self._parse_multiple_choice(variants_block)
        
        # 3. Установление соответствия (select)
        selects = variants_block.find_all('select')
        if selects:
            return self._parse_matching(variants_block)
        
        # По умолчанию - краткий ответ
        return TaskType.SHORT_ANSWER, {}
    
    def _parse_short_answer(self, block: BeautifulSoup) -> tuple:
        """Парсинг краткого ответа"""
        # Попытка найти единицу измерения
        answer_unit = None
        text_input = block.find('input', {'type': 'text', 'name': 'answer'})
        
        if text_input and text_input.parent:
            parent = text_input.parent
            text_after = parent.get_text()
            
            # Ищем текст после поля ввода
            match = re.search(r'</input>\s*([а-яА-Яa-zA-Z°]+)', str(parent))
            if match:
                answer_unit = match.group(1).strip()
        
        return TaskType.SHORT_ANSWER, {'answer_unit': answer_unit}
    
    def _parse_multiple_choice(self, block: BeautifulSoup) -> tuple:
        """Парсинг множественного выбора"""
        variants = []
        active_rows = block.find_all('tr', class_='active-distractor')
        
        for idx, row in enumerate(active_rows):
            checkbox = row.find('input', {'type': 'checkbox'})
            if not checkbox:
                continue
            
            # Текст варианта в последней td
            text_cell = row.find_all('td')[-1]
            variant_text = self._clean_text(text_cell.get_text()) if text_cell else ""
            
            input_name = checkbox.get('name', f'test{idx}')
            
            variants.append(AnswerVariant(
                index=idx,
                text=variant_text,
                input_name=input_name
            ))
        
        return TaskType.MULTIPLE_CHOICE, {'answer_variants': variants}
    
    def _parse_matching(self, block: BeautifulSoup) -> tuple:
        """Парсинг установления соответствия"""
        options = []
        choices = []
        
        selects = block.find_all('select')
        
        # Парсинг опций (А, Б, В...)
        for idx, select in enumerate(selects):
            select_name = select.get('name', f'ans{idx}')
            
            # Попытка найти букву и текст
            parent_td = select.find_parent('td')
            if parent_td:
                prev_td = parent_td.find_previous_sibling('td')
                if prev_td:
                    letter = self._clean_text(prev_td.get_text())
                else:
                    letter = chr(ord('А') + idx)
                
                text = f"Вариант {letter}"
                
                options.append(MatchingOption(
                    letter=letter,
                    text=text,
                    select_name=select_name
                ))
        
        # Парсинг вариантов выбора (1, 2, 3...)
        choice_rows = block.find_all('tr')
        for row in choice_rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                number_cell = cells[0]
                text_cell = cells[1]
                
                number_text = self._clean_text(number_cell.get_text())
                if re.match(r'^\d+\)', number_text):
                    number = number_text.replace(')', '').strip()
                    choice_text = self._clean_text(text_cell.get_text())
                    
                    choices.append(MatchingChoice(
                        number=number,
                        text=choice_text
                    ))
        
        return TaskType.MATCHING, {
            'matching_options': options,
            'matching_choices': choices
        }

