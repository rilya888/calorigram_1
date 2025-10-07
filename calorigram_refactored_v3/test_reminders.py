"""
Скрипт для тестирования системы напоминаний
"""
import asyncio
import sys
from reminder_sender import send_breakfast_reminders, send_lunch_reminders, send_dinner_reminders, send_test_reminder
from logging_config import get_logger

logger = get_logger(__name__)

async def test_all_reminders():
    """Тестирует все типы напоминаний"""
    print("\n🧪 Тестирование системы напоминаний...\n")
    
    # Тест завтрака
    print("📨 Отправка напоминаний о завтраке...")
    await send_breakfast_reminders()
    print("✅ Завершено\n")
    
    await asyncio.sleep(2)
    
    # Тест обеда
    print("📨 Отправка напоминаний об обеде...")
    await send_lunch_reminders()
    print("✅ Завершено\n")
    
    await asyncio.sleep(2)
    
    # Тест ужина
    print("📨 Отправка напоминаний об ужине...")
    await send_dinner_reminders()
    print("✅ Завершено\n")

async def test_single_user(telegram_id: int):
    """Тестирует напоминание для одного пользователя"""
    print(f"\n🧪 Отправка тестового напоминания пользователю {telegram_id}...\n")
    result = await send_test_reminder(telegram_id)
    if result:
        print(f"✅ Напоминание успешно отправлено пользователю {telegram_id}")
    else:
        print(f"❌ Ошибка отправки напоминания пользователю {telegram_id}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Если указан telegram_id, тестируем одного пользователя
        try:
            telegram_id = int(sys.argv[1])
            asyncio.run(test_single_user(telegram_id))
        except ValueError:
            print("❌ Ошибка: укажите корректный telegram_id")
            print("Использование: python test_reminders.py [telegram_id]")
    else:
        # Тестируем все типы напоминаний
        asyncio.run(test_all_reminders())
    
    print("\n✅ Тестирование завершено!")

