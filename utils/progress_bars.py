"""
Утилиты для создания прогресс-баров в Telegram
Создает визуальные индикаторы прогресса для БЖУ и калорий
"""
from typing import Tuple
from logging_config import get_logger

logger = get_logger(__name__)


def get_progress_emoji(progress: float) -> str:
    """
    Возвращает эмодзи в зависимости от прогресса
    
    Args:
        progress: Прогресс от 0.0 до 1.0
    
    Returns:
        Эмодзи индикатор
    """
    if progress >= 1.0:
        return "🟢"  # Зеленый - цель достигнута
    elif progress >= 0.8:
        return "🟡"  # Желтый - близко к цели
    elif progress >= 0.5:
        return "🟠"  # Оранжевый - средний прогресс
    else:
        return "🔴"  # Красный - далеко от цели


def create_progress_bar(current: float, target: float, width: int = 10) -> str:
    """
    Создает прогресс-бар из эмодзи
    
    Args:
        current: Текущее значение
        target: Целевое значение
        width: Ширина прогресс-бара
    
    Returns:
        Строка с прогресс-баром
    """
    try:
        if target == 0:
            return "░" * width
        
        progress = current / target
        # Ограничиваем заполнение бара до 100%, но показываем реальный процент
        filled = min(int(progress * width), width)
        
        bar = "█" * filled + "░" * (width - filled)
        percentage = int(progress * 100)
        
        return f"{bar} {percentage}%"
        
    except Exception as e:
        logger.error(f"Error creating progress bar: {e}")
        return "░" * width + " 0%"


def create_macro_progress_bar(current: float, target: float, name: str, unit: str = "г") -> str:
    """
    Создает детальный прогресс-бар для макронутриентов
    
    Args:
        current: Текущее значение
        target: Целевое значение
        name: Название макронутриента
        unit: Единица измерения
    
    Returns:
        Строка с прогресс-баром
    """
    try:
        if target == 0:
            return f"• {name}: {current}{unit} / {target}{unit} (не задано)"
        
        progress = current / target
        # Ограничиваем заполнение бара до 100%, но показываем реальный процент
        filled = min(int(progress * 10), 10)
        
        bar = "█" * filled + "░" * (10 - filled)
        percentage = int(progress * 100)
        emoji = get_progress_emoji(min(progress, 1.0))  # Эмодзи по ограниченному прогрессу
        
        return f"{emoji} {name}: {current}{unit} / {target}{unit} {bar} {percentage}%"
        
    except Exception as e:
        logger.error(f"Error creating macro progress bar: {e}")
        return f"• {name}: {current}{unit} / {target}{unit} (ошибка)"


def create_calorie_progress_bar(current: int, target: int) -> str:
    """
    Создает прогресс-бар для калорий
    
    Args:
        current: Текущие калории
        target: Целевые калории
    
    Returns:
        Строка с прогресс-баром калорий
    """
    try:
        if target == 0:
            return f"• Калории: {current} / {target} (не задано)"
        
        progress = current / target
        # Ограничиваем заполнение бара до 100%, но показываем реальный процент
        filled = min(int(progress * 10), 10)
        
        bar = "█" * filled + "░" * (10 - filled)
        percentage = int(progress * 100)
        emoji = get_progress_emoji(min(progress, 1.0))  # Эмодзи по ограниченному прогрессу
        
        remaining = target - current
        remaining_text = f"Остаток: {remaining} ккал" if remaining > 0 else f"Превышение: {abs(remaining)} ккал"
        
        return f"{emoji} Калории: {current} / {target} {bar} {percentage}%\n   {remaining_text}"
        
    except Exception as e:
        logger.error(f"Error creating calorie progress bar: {e}")
        return f"• Калории: {current} / {target} (ошибка)"


def create_meal_breakdown(meals_data: dict) -> str:
    """
    Создает разбивку по приемам пищи
    
    Args:
        meals_data: Словарь данных о приемах пищи (от get_daily_meals_by_type)
    
    Returns:
        Строка с разбивкой по приемам
    """
    try:
        if not meals_data:
            return "🍽️ **По приемам пищи:**\n   Записей о еде пока нет"
        
        result = "🍽️ **По приемам пищи:**\n"
        
        meal_emojis = {
            'meal_breakfast': '🌅',
            'meal_lunch': '☀️',
            'meal_dinner': '🌙',
            'meal_snack': '🍎'
        }
        
        meal_names = {
            'meal_breakfast': 'Завтрак',
            'meal_lunch': 'Обед',
            'meal_dinner': 'Ужин',
            'meal_snack': 'Перекусы'
        }
        
        # Определяем порядок приемов пищи
        meal_order = [
            'meal_breakfast',
            'meal_lunch', 
            'meal_dinner',
            'meal_snack'
        ]
        
        for meal_type in meal_order:
            if meal_type in meals_data:
                meal = meals_data[meal_type]
                meal_name = meal.get('name', 'Блюдо')
                calories = meal.get('calories', 0)
                protein = meal.get('protein', 0)
                fat = meal.get('fat', 0)
                carbs = meal.get('carbs', 0)
                dishes = meal.get('dishes', '')
                
                emoji = meal_emojis.get(meal_type, '🍽️')
                name = meal_names.get(meal_type, 'Прием пищи')
                
                result += f"{emoji} **{name}**: {calories} ккал\n"
                result += f"   • БЖУ: {protein:.1f}г/{fat:.1f}г/{carbs:.1f}г\n"
                if dishes:
                    result += f"   • Блюда: {dishes}\n"
                result += "\n"
            else:
                # Показываем пустой прием пищи
                emoji = meal_emojis.get(meal_type, '🍽️')
                name = meal_names.get(meal_type, 'Прием пищи')
                result += f"{emoji} **{name}**: 0 ккал\n\n"
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"Error creating meal breakdown: {e}")
        return "🍽️ **По приемам пищи:**\n   Ошибка загрузки данных"
