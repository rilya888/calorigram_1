"""
Калькулятор макронутриентов (БЖУ) для пользователей бота
Рассчитывает целевые БЖУ на основе веса, активности и целей
"""
from typing import Dict, Tuple
from logging_config import get_logger

logger = get_logger(__name__)


def calculate_daily_macros(weight: float, activity_level: str, goal: str, target_calories: int) -> Dict[str, float]:
    """
    Рассчитывает суточную норму БЖУ на основе параметров пользователя
    
    Args:
        weight: Вес пользователя в кг
        activity_level: Уровень активности (low, moderate, high)
        goal: Цель (lose_weight, maintain_weight, gain_weight)
        target_calories: Целевая калорийность в день
    
    Returns:
        Словарь с БЖУ в граммах и калориях
    """
    try:
        # Определяем коэффициенты на основе активности (5 уровней)
        if activity_level in ["Очень высокая", "very_high"]:
            protein_ratio = 1.8  # г/кг
            fat_ratio = 1.0      # г/кг
        elif activity_level in ["Высокая", "high"]:
            protein_ratio = 1.6  # г/кг
            fat_ratio = 0.9      # г/кг
        elif activity_level in ["Умеренная", "moderate"]:
            protein_ratio = 1.4  # г/кг
            fat_ratio = 0.8      # г/кг
        elif activity_level in ["Низкая", "low"]:
            protein_ratio = 1.2  # г/кг
            fat_ratio = 0.7      # г/кг
        else:  # Очень низкая
            protein_ratio = 1.0  # г/кг
            fat_ratio = 0.6      # г/кг
        
        # Корректируем под цель
        if goal == "lose_weight":
            protein_ratio += 0.2  # больше белка при похудении
        elif goal == "gain_weight":
            fat_ratio += 0.2      # больше жиров при наборе
        
        # Рассчитываем БЖУ в граммах
        protein_grams = weight * protein_ratio
        fat_grams = weight * fat_ratio
        
        # Рассчитываем калории от БЖ
        protein_calories = protein_grams * 4
        fat_calories = fat_grams * 9
        
        # Остаток калорий на углеводы
        remaining_calories = target_calories - protein_calories - fat_calories
        carb_grams = max(0, remaining_calories / 4)  # минимум 0г углеводов
        
        # Пересчитываем калории
        protein_calories = protein_grams * 4
        fat_calories = fat_grams * 9
        carb_calories = target_calories - protein_calories - fat_calories
        carb_grams = max(0, carb_calories / 4)
        
        result = {
            'protein': round(protein_grams, 1),
            'fat': round(fat_grams, 1),
            'carbs': round(carb_grams, 1),
            'protein_calories': round(protein_calories, 1),
            'fat_calories': round(fat_calories, 1),
            'carb_calories': round(carb_calories, 1)
        }
        
        logger.info(f"Calculated macros for weight={weight}kg, activity={activity_level}, goal={goal}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error calculating daily macros: {e}")
        # Возвращаем базовые значения в случае ошибки
        return {
            'protein': 100.0,
            'fat': 70.0,
            'carbs': 200.0,
            'protein_calories': 400.0,
            'fat_calories': 630.0,
            'carb_calories': 800.0
        }


def extract_macros_from_analysis(analysis_text: str) -> Tuple[int, float, float, float]:
    """
    Извлекает БЖУ из текста анализа ИИ
    
    Args:
        analysis_text: Текст анализа от ИИ
    
    Returns:
        Кортеж (калории, белки, жиры, углеводы)
    """
    try:
        import re
        
        # Извлекаем калории
        calories_match = re.search(r'Калорийность:\s*(\d+)\s*ккал', analysis_text)
        calories = int(calories_match.group(1)) if calories_match else 0
        
        # Извлекаем БЖУ из раздела "Общее БЖУ в блюде"
        protein_match = re.search(r'Белки:\s*([\d,]+)г', analysis_text)
        fat_match = re.search(r'Жиры:\s*([\d,]+)г', analysis_text)
        carbs_match = re.search(r'Углеводы:\s*([\d,]+)г', analysis_text)
        
        protein = float(protein_match.group(1).replace(',', '.')) if protein_match else 0.0
        fat = float(fat_match.group(1).replace(',', '.')) if fat_match else 0.0
        carbs = float(carbs_match.group(1).replace(',', '.')) if carbs_match else 0.0
        
        logger.info(f"Extracted macros from analysis: {calories} kcal, {protein}g protein, {fat}g fat, {carbs}g carbs")
        return calories, protein, fat, carbs
        
    except Exception as e:
        logger.error(f"Error extracting macros from analysis: {e}")
        return 0, 0.0, 0.0, 0.0


def get_macro_recommendations(current: Dict[str, float], target: Dict[str, float]) -> str:
    """
    Генерирует рекомендации по корректировке БЖУ
    
    Args:
        current: Текущие БЖУ
        target: Целевые БЖУ
    
    Returns:
        Текст с рекомендациями
    """
    try:
        recommendations = []
        
        # Проверяем белки
        protein_diff = target['protein'] - current['protein']
        if protein_diff > 5:
            recommendations.append(f"• Добавьте белка: +{protein_diff:.1f}г (творог, яйца, мясо)")
        elif protein_diff < -5:
            recommendations.append(f"• Уменьшите белки: {abs(protein_diff):.1f}г")
        
        # Проверяем жиры
        fat_diff = target['fat'] - current['fat']
        if fat_diff > 5:
            recommendations.append(f"• Добавьте жиров: +{fat_diff:.1f}г (орехи, авокадо, масло)")
        elif fat_diff < -5:
            recommendations.append(f"• Уменьшите жиры: {abs(fat_diff):.1f}г")
        
        # Проверяем углеводы
        carb_diff = target['carbs'] - current['carbs']
        if carb_diff > 10:
            recommendations.append(f"• Добавьте углеводов: +{carb_diff:.1f}г (фрукты, крупы, хлеб)")
        elif carb_diff < -10:
            recommendations.append(f"• Уменьшите углеводы: {abs(carb_diff):.1f}г")
        
        if not recommendations:
            return "• Отличный баланс БЖУ! Продолжайте в том же духе"
        
        return "\n".join(recommendations)
        
    except Exception as e:
        logger.error(f"Error generating macro recommendations: {e}")
        return "• Рекомендации недоступны"
