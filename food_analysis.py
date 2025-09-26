"""
Модуль для анализа еды с помощью ИИ
"""
import asyncio
from typing import Optional, Dict, Any, Tuple
from logging_config import get_logger
from api_client import api_client
from constants import MAX_IMAGE_SIZE, MAX_AUDIO_SIZE
from utils import sanitize_input

logger = get_logger(__name__)

class FoodAnalyzer:
    """Класс для анализа еды с помощью ИИ"""
    
    def __init__(self):
        self.api_client = api_client
    
    async def analyze_food_photo(self, photo_data: bytes) -> Dict[str, Any]:
        """Анализирует фото еды"""
        try:
            if not photo_data:
                return {"success": False, "error": "Пустые данные фото"}
            
            if len(photo_data) > MAX_IMAGE_SIZE:
                return {"success": False, "error": f"Файл слишком большой (макс. {MAX_IMAGE_SIZE // (1024*1024)}MB)"}
            
            async with self.api_client:
                analysis_result = await self.api_client.analyze_image(photo_data)
                
                if not analysis_result:
                    return {"success": False, "error": "Не удалось проанализировать фото"}
                
                # Извлекаем данные из анализа
                calories = self._extract_calories(analysis_result)
                dish_name = self._extract_dish_name(analysis_result)
                
                return {
                    "success": True,
                    "analysis": analysis_result,
                    "calories": calories,
                    "dish_name": dish_name
                }
                
        except Exception as e:
            logger.error(f"Error analyzing food photo: {e}")
            return {"success": False, "error": f"Ошибка анализа: {str(e)}"}
    
    async def analyze_food_text(self, text: str) -> Dict[str, Any]:
        """Анализирует текстовое описание еды"""
        try:
            # Валидация и очистка текста
            clean_text = sanitize_input(text, max_length=1000)
            if not clean_text or len(clean_text.strip()) < 10:
                return {"success": False, "error": "Описание слишком короткое"}
            
            # Дополнительная валидация для еды
            from validators import validator
            is_valid, error_msg, validated_text = validator.validate_food_description(clean_text)
            if not is_valid:
                return {"success": False, "error": error_msg}
            
            async with self.api_client:
                analysis_result = await self.api_client.analyze_text(validated_text)
                
                if not analysis_result:
                    return {"success": False, "error": "Не удалось проанализировать описание"}
                
                # Извлекаем данные из анализа
                calories = self._extract_calories(analysis_result)
                dish_name = self._extract_dish_name(analysis_result)
                
                # Проверяем качество анализа
                if not calories and not dish_name:
                    return {
                        "success": False, 
                        "error": "Не удалось определить калории и название блюда. Попробуйте более подробное описание с указанием ингредиентов и размера порции."
                    }
                
                return {
                    "success": True,
                    "analysis": analysis_result,
                    "calories": calories,
                    "dish_name": dish_name
                }
                
        except Exception as e:
            logger.error(f"Error analyzing food text: {e}")
            return {"success": False, "error": f"Ошибка анализа: {str(e)}"}
    
    async def analyze_food_voice(self, audio_data: bytes) -> Dict[str, Any]:
        """Анализирует голосовое описание еды"""
        try:
            if not audio_data:
                return {"success": False, "error": "Пустые аудио данные"}
            
            if len(audio_data) > MAX_AUDIO_SIZE:
                return {"success": False, "error": f"Аудио файл слишком большой (макс. {MAX_AUDIO_SIZE // (1024*1024)}MB)"}
            
            async with self.api_client:
                analysis_result = await self.api_client.analyze_voice(audio_data)
                
                if not analysis_result:
                    return {"success": False, "error": "Не удалось проанализировать голосовое сообщение"}
                
                # Извлекаем данные из анализа
                calories = self._extract_calories(analysis_result)
                dish_name = self._extract_dish_name(analysis_result)
                
                return {
                    "success": True,
                    "analysis": analysis_result,
                    "calories": calories,
                    "dish_name": dish_name
                }
                
        except Exception as e:
            logger.error(f"Error analyzing food voice: {e}")
            return {"success": False, "error": f"Ошибка анализа: {str(e)}"}
    
    def _extract_calories(self, analysis_text: str) -> Optional[int]:
        """Извлекает калории из текста анализа"""
        import re
        
        try:
            if not analysis_text or not isinstance(analysis_text, str):
                return None
                
            # Ищем паттерны для общей калорийности
            patterns = [
                r'Общая калорийность:\s*(\d+)\s*ккал',
                r'Общее количество калорий:\s*(\d+)\s*ккал',
                r'Калорийность блюда:\s*(\d+)\s*ккал',
                r'Калорийность:\s*(\d+)\s*ккал\s*$',
                r'(\d+)\s*ккал\s*$',
                r'калорийность:\s*(\d+)',
                r'калорий:\s*(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, analysis_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    try:
                        calories = int(match.group(1))
                        if 10 <= calories <= 10000:
                            return calories
                    except ValueError:
                        continue
            
            # Fallback поиск
            fallback_patterns = [r'(\d+)\s*ккал', r'калорийность:\s*(\d+)', r'калорий:\s*(\d+)']
            
            for pattern in fallback_patterns:
                match = re.search(pattern, analysis_text, re.IGNORECASE)
                if match:
                    try:
                        calories = int(match.group(1))
                        if 10 <= calories <= 10000:
                            return calories
                    except ValueError:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting calories: {e}")
            return None
    
    def _extract_dish_name(self, analysis_text: str) -> Optional[str]:
        """Извлекает название блюда из текста анализа"""
        import re
        
        try:
            pattern = r'Название:\s*([^\n]+)'
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            return None
        except Exception as e:
            logger.error(f"Error extracting dish name: {e}")
            return None

# Глобальный экземпляр анализатора
food_analyzer = FoodAnalyzer()

