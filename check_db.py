#!/usr/bin/env python3
"""
Скрипт для проверки данных в базе
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection

def check_user_data(telegram_id: int):
    """Проверяет данные пользователя в базе"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем пользователя
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()
            if user:
                print(f"👤 Пользователь найден: {dict(user)}")
            else:
                print(f"❌ Пользователь с ID {telegram_id} не найден")
                return
            
            # Проверяем записи о приемах пищи за сегодня
            cursor.execute('''
                SELECT * FROM meals 
                WHERE telegram_id = ? AND DATE(created_at) = DATE('now')
                ORDER BY created_at DESC
            ''', (telegram_id,))
            
            meals = cursor.fetchall()
            print(f"\n🍽️ Записей о приемах пищи за сегодня: {len(meals)}")
            
            for i, meal in enumerate(meals, 1):
                meal_dict = dict(meal)
                print(f"\n{i}. {meal_dict.get('meal_name', 'Неизвестно')} ({meal_dict.get('meal_type', 'Неизвестно')})")
                print(f"   Блюдо: {meal_dict.get('dish_name', 'Неизвестно')}")
                print(f"   Калории: {meal_dict.get('calories', 0)}")
                print(f"   Белки: {meal_dict.get('protein', 0)}г")
                print(f"   Жиры: {meal_dict.get('fat', 0)}г")
                print(f"   Углеводы: {meal_dict.get('carbs', 0)}г")
                print(f"   Дата: {meal_dict.get('created_at', 'Неизвестно')}")
                print(f"   Тип анализа: {meal_dict.get('analysis_type', 'Неизвестно')}")
            
            # Проверяем общую статистику
            cursor.execute('''
                SELECT 
                    SUM(calories) as total_calories,
                    SUM(protein) as total_protein,
                    SUM(fat) as total_fat,
                    SUM(carbs) as total_carbs,
                    COUNT(*) as meals_count
                FROM meals 
                WHERE telegram_id = ? AND DATE(created_at) = DATE('now')
            ''', (telegram_id,))
            
            stats = cursor.fetchone()
            if stats:
                stats_dict = dict(stats)
                print(f"\n📊 Общая статистика за сегодня:")
                print(f"   Калории: {stats_dict.get('total_calories', 0)}")
                print(f"   Белки: {stats_dict.get('total_protein', 0)}г")
                print(f"   Жиры: {stats_dict.get('total_fat', 0)}г")
                print(f"   Углеводы: {stats_dict.get('total_carbs', 0)}г")
                print(f"   Количество записей: {stats_dict.get('meals_count', 0)}")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python check_db.py <telegram_id>")
        return
    
    try:
        telegram_id = int(sys.argv[1])
        check_user_data(telegram_id)
    except ValueError:
        print("❌ Ошибка: telegram_id должен быть числом")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
