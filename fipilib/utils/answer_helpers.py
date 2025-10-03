"""
Вспомогательные функции для работы с ответами
"""


class AnswerHelper:
    """Утилиты для работы с ответами"""
    
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
            total: Всего вариантов
        
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

