"""
Сервис для анализа еды через AI
"""
import logging
import re
from typing import Optional, Tuple
from api_client import APIClient, api_client
from constants import MAX_IMAGE_SIZE
from logging_config import get_logger

logger = get_logger(__name__)

# Константы для валидации
MAX_TEXT_LENGTH = 1000  # Максимальная длина текстового описания


# ==================== UTILITY FUNCTIONS ====================

def extract_weight_from_description(description: str) -> Optional[float]:
    """Извлекает вес из описания блюда"""
    try:
        # Паттерны для поиска веса
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(?:г|гр|грамм|gram)',
            r'(\d+(?:[.,]\d+)?)\s*(?:кг|килограмм|kg)',
            r'(\d+(?:[.,]\d+)?)\s*(?:мл|ml)',
            r'(\d+(?:[.,]\d+)?)\s*(?:л|литр|liter)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                weight = float(match.group(1).replace(',', '.'))
                # Конвертируем кг и л в г/мл
                if 'кг' in pattern or 'kg' in pattern or 'литр' in pattern or 'liter' in pattern:
                    weight *= 1000
                return weight
        
        return None
    except Exception as e:
        logger.error(f"Error extracting weight: {e}")
        return None


def extract_calories_per_100g_from_analysis(analysis_text: str) -> Optional[int]:
    """Извлекает калорийность на 100г из анализа"""
    try:
        # Ищем калорийность на 100г
        patterns = [
            r'Калорийность на 100г:\s*(\d+)\s*ккал',
            r'на 100г:\s*(\d+)\s*ккал',
            r'100г.*?(\d+)\s*ккал'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE | re.MULTILINE)
            if match:
                calories = int(match.group(1))
                if 0 < calories < 10000:  # Разумная проверка
                    logger.info(f"Extracted calories per 100g: {calories} from pattern: {pattern}")
                    return calories
        
        return None
    except Exception as e:
        logger.error(f"Error extracting calories per 100g: {e}")
        return None


def extract_calories_from_analysis(analysis_text: str) -> Optional[int]:
    """Извлекает общую калорийность из анализа"""
    try:
        logger.info(f"Extracting calories from analysis text: {analysis_text[:100]}...")
        
        # Приоритетные паттерны
        priority_patterns = [
            # Точные паттерны с якорями
            r'Калорийность:\s*(\d+)\s*ккал\s*$',
            r'Общая калорийность:\s*(\d+)\s*ккал',
            r'Калорийность блюда:\s*(\d+)\s*ккал',
            r'Всего калорий:\s*(\d+)\s*ккал',
        ]
        
        # Попытка извлечь по приоритетным паттернам
        for pattern in priority_patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE | re.MULTILINE)
            if match:
                calories = int(match.group(1))
                if 0 < calories < 10000:
                    logger.info(f"Extracted calories: {calories} from pattern: {pattern}")
                    return calories
        
        # Запасные паттерны
        fallback_patterns = [
            r'калорийность.*?(\d+)\s*ккал',
            r'(\d+)\s*ккал',
        ]
        
        for pattern in fallback_patterns:
            matches = re.findall(pattern, analysis_text, re.IGNORECASE)
            if matches:
                # Берем последнее значение (обычно это общая калорийность)
                calories = int(matches[-1] if isinstance(matches[-1], str) else matches[-1][0])
                if 0 < calories < 10000:
                    logger.info(f"Extracted calories (fallback): {calories} from pattern: {pattern}")
                    return calories
        
        logger.warning("Could not extract calories from analysis")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting calories: {e}")
        return None


def extract_macros_from_analysis(analysis_text: str) -> Tuple[int, float, float, float]:
    """Извлекает БЖУ из анализа ИИ"""
    try:
        logger.info(f"Extracting macros from analysis text: {analysis_text[:100]}...")
        
        # Извлекаем калории
        calories = extract_calories_from_analysis(analysis_text) or 0
        
        # Извлекаем БЖУ из раздела "Общее БЖУ в блюде"
        protein_patterns = [
            r'📈 Общее БЖУ в блюде:.*?• Белки:\s*([\d,]+)г',
            r'Общее БЖУ в блюде:.*?• Белки:\s*([\d,]+)г',
            r'• Белки:\s*([\d,]+)г',
            r'Белки:\s*([\d,]+)г',
            r'Белки:\s*([\d,]+)\s*г',
        ]
        
        fat_patterns = [
            r'📈 Общее БЖУ в блюде:.*?• Жиры:\s*([\d,]+)г',
            r'Общее БЖУ в блюде:.*?• Жиры:\s*([\d,]+)г',
            r'• Жиры:\s*([\d,]+)г',
            r'Жиры:\s*([\d,]+)г',
            r'Жиры:\s*([\d,]+)\s*г',
        ]
        
        carbs_patterns = [
            r'📈 Общее БЖУ в блюде:.*?• Углеводы:\s*([\d,]+)г',
            r'Общее БЖУ в блюде:.*?• Углеводы:\s*([\d,]+)г',
            r'• Углеводы:\s*([\d,]+)г',
            r'Углеводы:\s*([\d,]+)г',
            r'Углеводы:\s*([\d,]+)\s*г',
        ]
        
        protein = 0.0
        fat = 0.0
        carbs = 0.0
        
        # Извлекаем белки
        for pattern in protein_patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                protein = float(match.group(1).replace(',', '.'))
                break
        
        # Извлекаем жиры
        for pattern in fat_patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                fat = float(match.group(1).replace(',', '.'))
                break
        
        # Извлекаем углеводы
        for pattern in carbs_patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                carbs = float(match.group(1).replace(',', '.'))
                break
        
        logger.info(f"Extracted macros: {calories} kcal, {protein}g protein, {fat}g fat, {carbs}g carbs")
        return calories, protein, fat, carbs
        
    except Exception as e:
        logger.error(f"Error extracting macros from analysis: {e}")
        return 0, 0.0, 0.0, 0.0


def extract_dish_name_from_analysis(analysis_text: str) -> Optional[str]:
    """Извлекает название блюда из анализа"""
    try:
        pattern = r'Название:\s*(.+?)(?:\n|$)'
        match = re.search(pattern, analysis_text)
        if match:
            return match.group(1).strip()
        return None
    except Exception as e:
        logger.error(f"Error extracting dish name: {e}")
        return None


def parse_quantity_from_description(description: str) -> Tuple[float, str]:
    """
    Парсит количество из описания блюда
    
    Returns:
        Tuple[float, str]: (количество, единица измерения)
    """
    try:
        # Паттерны для различных единиц измерения
        patterns = {
            'г': r'(\d+(?:[.,]\d+)?)\s*(?:г|гр|грамм|gram)',
            'кг': r'(\d+(?:[.,]\d+)?)\s*(?:кг|килограмм|kg)',
            'мл': r'(\d+(?:[.,]\d+)?)\s*(?:мл|ml)',
            'л': r'(\d+(?:[.,]\d+)?)\s*(?:л|литр|liter)',
            'шт': r'(\d+(?:[.,]\d+)?)\s*(?:шт|штук|штуки|piece|pieces)',
            'порц': r'(\d+(?:[.,]\d+)?)\s*(?:порц|порция|порций|serving|servings)',
            'ст': r'(\d+(?:[.,]\d+)?)\s*(?:ст|стакан|стаканов|glass|glasses)',
            'ч_л': r'(\d+(?:[.,]\d+)?)\s*(?:ч\.л|чайн\.л|чайная ложка|teaspoon)',
            'ст_л': r'(\d+(?:[.,]\d+)?)\s*(?:ст\.л|столов\.л|столовая ложка|tablespoon)',
        }
        
        for unit, pattern in patterns.items():
            match = re.search(pattern, description.lower())
            if match:
                quantity = float(match.group(1).replace(',', '.'))
                return quantity, unit
        
        # Если не найдено, возвращаем значения по умолчанию
        return 1.0, 'порц'
        
    except Exception as e:
        logger.error(f"Error parsing quantity: {e}")
        return 1.0, 'порц'


def is_valid_analysis(analysis_text: str) -> bool:
    """Проверяет, валиден ли результат анализа"""
    return bool(analysis_text and len(analysis_text) > 20 and ('калори' in analysis_text.lower() or 'ккал' in analysis_text.lower()))


def clean_markdown_text(text: str) -> str:
    """Очищает текст от markdown разметки для отображения"""
    if not text:
        return ""
    
    # Удаляем только markdown символы, сохраняя структуру текста
    cleaned = text.replace('**', '').replace('__', '').replace('*', '').replace('_', '')
    
    # Удаляем лишние пробелы ТОЛЬКО внутри строк, не трогая переносы
    lines = cleaned.split('\n')
    cleaned_lines = [re.sub(r'  +', ' ', line).strip() for line in lines]
    
    return '\n'.join(cleaned_lines)


def remove_explanations_from_analysis(text: str) -> str:
    """Удаляет пояснения из анализа, оставляя только данные"""
    if not text:
        return ""
    
    # Удаляем строки с пояснениями
    lines = text.split('\n')
    filtered_lines = []
    
    skip_patterns = [
        r'примечани',
        r'рекомендац',
        r'совет',
        r'обрати внимание',
        r'важно',
    ]
    
    for line in lines:
        # Пропускаем строки с пояснениями
        if any(re.search(pattern, line.lower()) for pattern in skip_patterns):
            continue
        filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


# ==================== AI ANALYSIS FUNCTIONS ====================

async def analyze_food_photo(image_data: bytes):
    """Анализирует фото еды через AI"""
    try:
        # Валидация размера изображения
        if not image_data:
            logger.error("Empty image data provided")
            return None
            
        if len(image_data) > MAX_IMAGE_SIZE:
            logger.error(f"Image too large: {len(image_data)} bytes (max: {MAX_IMAGE_SIZE})")
            return None
        
        logger.info("Starting food photo analysis...")
        
        async with api_client:
            result = await api_client.analyze_image(image_data)
        
        logger.info(f"Photo analysis successful, result length: {len(result) if result else 0}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing food photo: {e}")
        return None


async def analyze_food_text(description: str):
    """Анализирует текстовое описание еды через AI"""
    try:
        # Валидация входных данных
        if not description or not isinstance(description, str):
            logger.error(f"Invalid description provided: type={type(description)}, value='{description}'")
            return None
        
        description = description.strip()
        
        if len(description) < 5:
            logger.error(f"Description too short: length={len(description)}, content='{description}'")
            return None
            
        if len(description) > MAX_TEXT_LENGTH:
            logger.error(f"Description too long: {len(description)} chars (max: {MAX_TEXT_LENGTH})")
            return None
        
        logger.info(f"Starting text analysis for description: {description[:50]}...")
        
        async with api_client:
            result = await api_client.analyze_text(description)
        
        logger.info(f"Text analysis successful, result length: {len(result) if result else 0}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing food text: {e}")
        return None


async def analyze_food_supplement(combined_prompt: str):
    """Анализирует комбинированный промпт для дополнения анализа фото"""
    try:
        # Валидация входных данных
        if not combined_prompt or not isinstance(combined_prompt, str):
            logger.error(f"Invalid combined prompt provided: type={type(combined_prompt)}, value='{combined_prompt}'")
            return None
        
        # Для дополнительного текста к фото используем более мягкую валидацию
        if len(combined_prompt.strip()) < 3:
            logger.error(f"Combined prompt too short: length={len(combined_prompt.strip())}, content='{combined_prompt.strip()}'")
            return None
            
        logger.info("Starting food supplement analysis...")
        
        async with api_client:
            result = await api_client.analyze_text(combined_prompt)
        
        logger.info(f"Supplement analysis successful, result length: {len(result) if result else 0}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing food supplement: {e}")
        return None


async def transcribe_voice(audio_data: bytes):
    """Транскрибирует голосовое сообщение"""
    try:
        if not audio_data:
            logger.error("Empty audio data provided")
            return None
        
        logger.info("Starting voice transcription...")
        
        async with api_client:
            result = await api_client.analyze_voice(audio_data, None, None)
        
        logger.info(f"Voice transcription result: {result[:100] if result else None}...")
        return result
        
    except Exception as e:
        logger.error(f"Error transcribing voice: {e}")
        return None

