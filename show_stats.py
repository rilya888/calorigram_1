#!/usr/bin/env python3
"""
Скрипт для показа статистики пользователя за сегодня
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_daily_meals_by_type, get_daily_macros, get_user_target_macros, get_user_by_telegram_id
from datetime import datetime

def show_user_stats(telegram_id: int):
    """Показывает статистику пользователя за сегодня"""
    try:
        # Проверяем, существует ли пользователь
        user_data = get_user_by_telegram_id(telegram_id)
        if not user_data:
            print(f"❌ Пользователь с ID {telegram_id} не найден в базе данных")
            return
        
        # Преобразуем Row в словарь
        if hasattr(user_data, 'keys'):
            user_dict = dict(user_data)
        else:
            user_dict = user_data
        
        print(f"👤 Пользователь: {user_dict.get('first_name', 'Неизвестно')} {user_dict.get('last_name', '')}")
        print(f"📅 Статистика за сегодня ({datetime.now().strftime('%d.%m.%Y')}):")
        print("=" * 50)
        
        # Получаем данные за сегодня
        meals_data = get_daily_meals_by_type(telegram_id)
        current_macros = get_daily_macros(telegram_id)
        target_macros = get_user_target_macros(telegram_id)
        
        if not meals_data:
            print("📊 Нет записей о приемах пищи за сегодня")
            return
        
        # Показываем статистику по приемам пищи
        meal_names = {
            'meal_breakfast': '🌅 Завтрак',
            'meal_lunch': '☀️ Обед', 
            'meal_dinner': '🌙 Ужин',
            'meal_snack': '🍎 Перекус'
        }
        
        total_calories = 0
        total_protein = 0
        total_fat = 0
        total_carbs = 0
        
        print("\n🍽️ **Приемы пищи:**")
        for meal_type, meal_name in meal_names.items():
            if meal_type in meals_data:
                meal = meals_data[meal_type]
                # Преобразуем Row в словарь если нужно
                if hasattr(meal, 'keys'):
                    meal_dict = dict(meal)
                else:
                    meal_dict = meal
                
                calories = meal_dict.get('total_calories', 0)
                protein = meal_dict.get('total_protein', 0)
                fat = meal_dict.get('total_fat', 0)
                carbs = meal_dict.get('total_carbs', 0)
                dishes = meal_dict.get('dishes', '')
                
                total_calories += calories
                total_protein += protein
                total_fat += fat
                total_carbs += carbs
                
                print(f"\n{meal_name}:")
                print(f"  🔥 Калории: {calories:.0f} ккал")
                print(f"  🥩 Белки: {protein:.1f}г")
                print(f"  🧈 Жиры: {fat:.1f}г")
                print(f"  🍞 Углеводы: {carbs:.1f}г")
                print(f"  🍽️ Блюда: {dishes}")
            else:
                print(f"\n{meal_name}: 0 ккал")
        
        # Общая статистика
        print(f"\n📊 **Общая статистика за день:**")
        print(f"🔥 Всего калорий: {total_calories:.0f} ккал")
        print(f"🥩 Белки: {total_protein:.1f}г")
        print(f"🧈 Жиры: {total_fat:.1f}г")
        print(f"🍞 Углеводы: {total_carbs:.1f}г")
        
        # Сравнение с целевыми значениями
        if target_macros:
            print(f"\n🎯 **Целевые значения:**")
            print(f"🔥 Калории: {target_macros['calories']:.0f} ккал")
            print(f"🥩 Белки: {target_macros['protein']:.1f}г")
            print(f"🧈 Жиры: {target_macros['fat']:.1f}г")
            print(f"🍞 Углеводы: {target_macros['carbs']:.1f}г")
            
            # Проценты от цели
            calorie_percent = (total_calories / target_macros['calories']) * 100 if target_macros['calories'] > 0 else 0
            protein_percent = (total_protein / target_macros['protein']) * 100 if target_macros['protein'] > 0 else 0
            fat_percent = (total_fat / target_macros['fat']) * 100 if target_macros['fat'] > 0 else 0
            carbs_percent = (total_carbs / target_macros['carbs']) * 100 if target_macros['carbs'] > 0 else 0
            
            print(f"\n📈 **Прогресс (% от цели):**")
            print(f"🔥 Калории: {calorie_percent:.1f}%")
            print(f"🥩 Белки: {protein_percent:.1f}%")
            print(f"🧈 Жиры: {fat_percent:.1f}%")
            print(f"🍞 Углеводы: {carbs_percent:.1f}%")
        
    except Exception as e:
        print(f"❌ Ошибка при получении статистики: {e}")

def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python show_stats.py <telegram_id>")
        print("Пример: python show_stats.py 160308091")
        return
    
    try:
        telegram_id = int(sys.argv[1])
        show_user_stats(telegram_id)
    except ValueError:
        print("❌ Ошибка: telegram_id должен быть числом")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
