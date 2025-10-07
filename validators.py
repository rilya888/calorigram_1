"""
Модуль для валидации данных
"""
from typing import Tuple, Optional
from logging_config import get_logger
from constants import MIN_AGE, MAX_AGE, MIN_HEIGHT, MAX_HEIGHT, MIN_WEIGHT, MAX_WEIGHT, ACTIVITY_LEVELS, GENDERS
from utils import validate_telegram_id

logger = get_logger(__name__)

class DataValidator:
    """Класс для валидации различных типов данных"""
    
    @staticmethod
    def validate_user_input(telegram_id: int, name: str, gender: str, age: int, 
                           height: float, weight: float, activity_level: str) -> Tuple[bool, str]:
        """Валидирует входные данные пользователя"""
        try:
            # Проверяем telegram_id
            if not validate_telegram_id(telegram_id):
                return False, "Неверный Telegram ID"
            
            # Проверяем имя
            if not name or len(name.strip()) < 2 or len(name.strip()) > 50:
                return False, "Имя должно содержать от 2 до 50 символов"
            
            # Проверяем пол
            if gender not in GENDERS:
                return False, "Неверный пол"
            
            # Проверяем возраст
            if not isinstance(age, int) or age < MIN_AGE or age > MAX_AGE:
                return False, f"Возраст должен быть от {MIN_AGE} до {MAX_AGE} лет"
            
            # Проверяем рост
            if not isinstance(height, (int, float)) or height < MIN_HEIGHT or height > MAX_HEIGHT:
                return False, f"Рост должен быть от {MIN_HEIGHT} до {MAX_HEIGHT} см"
            
            # Проверяем вес
            if not isinstance(weight, (int, float)) or weight < MIN_WEIGHT or weight > MAX_WEIGHT:
                return False, f"Вес должен быть от {MIN_WEIGHT} до {MAX_WEIGHT} кг"
            
            # Проверяем уровень активности
            if activity_level not in ACTIVITY_LEVELS:
                return False, "Неверный уровень активности"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error validating user input: {e}")
            return False, "Ошибка валидации данных"
    
    @staticmethod
    def validate_meal_data(meal_type: str, meal_name: str, calories: int) -> Tuple[bool, str]:
        """Валидирует данные о приеме пищи"""
        try:
            # Проверяем тип приема пищи
            valid_meal_types = ['meal_breakfast', 'meal_lunch', 'meal_dinner', 'meal_snack']
            if not meal_type or meal_type not in valid_meal_types:
                return False, "Неверный тип приема пищи"
            
            # Проверяем название блюда
            if not meal_name or not isinstance(meal_name, str):
                return False, "Название блюда не может быть пустым"
            
            clean_name = meal_name.strip()
            if len(clean_name) < 2:
                return False, "Название блюда должно содержать минимум 2 символа"
            
            if len(clean_name) > 100:
                return False, "Название блюда слишком длинное (максимум 100 символов)"
            
            # Проверяем на наличие только специальных символов
            if not any(c.isalnum() for c in clean_name):
                return False, "Название блюда должно содержать буквы или цифры"
            
            # Проверяем калории
            if not isinstance(calories, int):
                return False, "Калории должны быть целым числом"
            
            if calories < 0:
                return False, "Калории не могут быть отрицательными"
            
            if calories > 50000:  # Увеличиваем лимит для экстремальных случаев
                return False, "Калории превышают разумный лимит (максимум 50000)"
            
            # Проверяем на разумные значения
            if calories == 0:
                return False, "Калории не могут быть равны нулю"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error validating meal data: {e}")
            return False, "Ошибка валидации данных о приеме пищи"
    
    @staticmethod
    def validate_file_size(file_data: bytes, file_type: str, max_size: int) -> Tuple[bool, str]:
        """Валидирует размер файла"""
        try:
            if not file_data:
                return False, "Пустые данные файла"
            
            if len(file_data) > max_size:
                size_mb = max_size // (1024 * 1024)
                return False, f"Файл слишком большой (максимум {size_mb}MB)"
            
            if len(file_data) < 100:
                return False, "Файл слишком маленький, возможно поврежден"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error validating file size: {e}")
            return False, "Ошибка валидации файла"
    
    @staticmethod
    def validate_text_input(text: str, min_length: int = 10, max_length: int = 1000) -> Tuple[bool, str]:
        """Валидирует текстовый ввод"""
        try:
            if not text:
                return False, "Пустой текст"
            
            clean_text = text.strip()
            if len(clean_text) < min_length:
                return False, f"Текст слишком короткий (минимум {min_length} символов)"
            
            if len(clean_text) > max_length:
                return False, f"Текст слишком длинный (максимум {max_length} символов)"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error validating text input: {e}")
            return False, "Ошибка валидации текста"
    
    @staticmethod
    def validate_food_description(text: str) -> Tuple[bool, str, str]:
        """Валидирует описание еды для анализа"""
        try:
            if not text:
                return False, "Пустой текст", ""
            
            # Очищаем и нормализуем текст
            clean_text = text.strip()
            
            # Проверяем минимальную длину
            if len(clean_text) < 5:
                return False, "Описание слишком короткое (минимум 5 символов)", clean_text
            
            # Проверяем максимальную длину
            if len(clean_text) > 1000:
                return False, "Описание слишком длинное (максимум 1000 символов)", clean_text
            
            # Проверяем на наличие только цифр или специальных символов
            if clean_text.replace(' ', '').replace('-', '').replace('+', '').replace('.', '').replace(',', '').isdigit():
                return False, "Описание содержит только цифры. Укажите название блюда и ингредиенты.", clean_text
            
            # Проверяем на наличие осмысленных слов (минимум 2 слова)
            words = [w for w in clean_text.split() if len(w) > 1 and w.isalpha()]
            if len(words) < 2:
                return False, "Укажите более подробное описание блюда с ингредиентами", clean_text
            
            # Проверяем на спам или повторяющиеся символы
            if len(set(clean_text)) < 3:
                return False, "Описание содержит слишком много повторяющихся символов", clean_text
            
            # Проверяем на наличие ключевых слов для еды
            food_keywords = [
                'еда', 'блюдо', 'пища', 'продукт', 'ингредиент', 'состав',
                'мясо', 'рыба', 'курица', 'говядина', 'свинина', 'баранина',
                'овощ', 'фрукт', 'яблоко', 'банан', 'апельсин', 'помидор',
                'картофель', 'морковь', 'лук', 'чеснок', 'перец', 'капуста',
                'молоко', 'сыр', 'творог', 'йогурт', 'кефир', 'сметана',
                'хлеб', 'булка', 'крупа', 'рис', 'гречка', 'овес', 'пшено',
                'макароны', 'лапша', 'спагетти', 'пельмени', 'вареники',
                'суп', 'борщ', 'щи', 'солянка', 'рассольник', 'окрошка',
                'салат', 'винегрет', 'оливье', 'цезарь', 'греческий',
                'каша', 'овсянка', 'манка', 'перловка', 'ячневая',
                'котлета', 'бифштекс', 'стейк', 'шашлык', 'отбивная',
                'рыба', 'лосось', 'треска', 'сельдь', 'скумбрия', 'тунец',
                'яйцо', 'омлет', 'глазунья', 'яичница', 'пашот',
                'масло', 'растительное', 'сливочное', 'подсолнечное', 'оливковое',
                'соль', 'сахар', 'перец', 'специи', 'приправы', 'травы',
                'г', 'кг', 'грамм', 'килограмм', 'литр', 'мл', 'стакан',
                'порция', 'кусок', 'штука', 'тарелка', 'чашка', 'ложка'
            ]
            
            text_lower = clean_text.lower()
            has_food_keywords = any(keyword in text_lower for keyword in food_keywords)
            
            if not has_food_keywords:
                return False, "Не удалось распознать описание еды. Укажите название блюда и основные ингредиенты.", clean_text
            
            return True, "OK", clean_text
            
        except Exception as e:
            logger.error(f"Error validating food description: {e}")
            return False, "Ошибка валидации описания", text

# Глобальный экземпляр валидатора
validator = DataValidator()

