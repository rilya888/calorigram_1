"""
Функции для отправки напоминаний о приемах пищи
"""
import asyncio
from datetime import datetime
from typing import List, Tuple
import pytz
from logging_config import get_logger
from database import get_users_with_reminders_enabled, has_user_added_meal_today
from config import BOT_TOKEN

logger = get_logger(__name__)

# Импортируем telegram только когда нужно
try:
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    Bot = None
    TelegramError = Exception

# Создаем глобальный объект бота
bot_instance = None

def get_bot():
    """Получает экземпляр бота"""
    global bot_instance
    if bot_instance is None and Bot:
        bot_instance = Bot(token=BOT_TOKEN)
    return bot_instance

async def send_meal_reminder(telegram_id: int, meal_type: str, meal_name: str, emoji: str):
    """Отправляет напоминание о приеме пищи конкретному пользователю"""
    try:
        bot = get_bot()
        if not bot:
            logger.error("Bot instance not available")
            return False
            
        # Проверяем, добавил ли пользователь уже этот прием пищи сегодня
        if has_user_added_meal_today(telegram_id, meal_type):
            logger.info(f"User {telegram_id} already added {meal_type} today, skipping reminder")
            return True
            
        message = f"""
{emoji} **Время {meal_name.lower()}!**

Не забудьте добавить информацию о {meal_name.lower()} в бот.

📱 **Как добавить:**
• Нажмите /start
• Выберите "Добавить блюдо"
• Выберите "{meal_name}"
• Отправьте фото, голос или текст

💡 **Совет:** Регулярное отслеживание поможет вам лучше контролировать питание!
        """
        
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode='Markdown'
        )
        
        logger.info(f"Reminder sent to user {telegram_id} for {meal_type}")
        return True
        
    except TelegramError as e:
        if "chat not found" in str(e).lower() or "bot was blocked" in str(e).lower():
            logger.warning(f"User {telegram_id} blocked bot or chat not found: {e}")
        else:
            logger.error(f"Telegram error sending reminder to {telegram_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending reminder to {telegram_id}: {e}")
        return False

async def send_breakfast_reminders():
    """Отправляет напоминания о завтраке в 9:00"""
    await send_meal_reminders_for_type('meal_breakfast', 'Завтрак', '🌅')

async def send_lunch_reminders():
    """Отправляет напоминания об обеде в 14:00"""
    await send_meal_reminders_for_type('meal_lunch', 'Обед', '☀️')

async def send_dinner_reminders():
    """Отправляет напоминания об ужине в 19:00"""
    await send_meal_reminders_for_type('meal_dinner', 'Ужин', '🌙')

async def send_meal_reminders_for_type(meal_type: str, meal_name: str, emoji: str):
    """Отправляет напоминания о конкретном приеме пищи всем пользователям с включенными напоминаниями"""
    try:
        logger.info(f"Starting {meal_name.lower()} reminders...")
        
        # Получаем всех пользователей с включенными напоминаниями
        users = get_users_with_reminders_enabled()
        
        if not users:
            logger.info("No users with reminders enabled")
            return
            
        logger.info(f"Found {len(users)} users with reminders enabled")
        
        # Отправляем напоминания всем пользователям
        tasks = []
        for user_data in users:
            telegram_id = user_data[0]
            timezone = user_data[2]  # timezone находится на индексе 2 (0=telegram_id, 1=name, 2=timezone)
            
            # Проверяем, что время в часовом поясе пользователя соответствует времени напоминания
            if is_reminder_time(timezone, meal_type):
                task = send_meal_reminder(telegram_id, meal_type, meal_name, emoji)
                tasks.append(task)
            else:
                logger.debug(f"Skipping user {telegram_id} - not reminder time in timezone {timezone}")
        
        if tasks:
            # Отправляем все напоминания параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for result in results if result is True)
            failed = len(results) - successful
            
            logger.info(f"Breakfast reminders completed: {successful} successful, {failed} failed")
        else:
            logger.info(f"No users to send {meal_name.lower()} reminders to")
            
    except Exception as e:
        logger.error(f"Error sending {meal_name.lower()} reminders: {e}")

def is_reminder_time(timezone_str: str, meal_type: str) -> bool:
    """Проверяет, наступило ли время для отправки напоминания в данном часовом поясе"""
    try:
        # Определяем время напоминания
        reminder_hours = {
            'meal_breakfast': 9,
            'meal_lunch': 14,
            'meal_dinner': 19
        }
        
        target_hour = reminder_hours.get(meal_type, 9)
        
        # Получаем текущее время в часовом поясе пользователя
        user_tz = pytz.timezone(timezone_str)
        now = datetime.now(user_tz)
        
        # Проверяем, что сейчас время напоминания (с допуском в 1 час)
        current_hour = now.hour
        return current_hour == target_hour
        
    except Exception as e:
        logger.error(f"Error checking reminder time for timezone {timezone_str}: {e}")
        return False

async def send_test_reminder(telegram_id: int):
    """Отправляет тестовое напоминание пользователю"""
    try:
        bot = get_bot()
        if not bot:
            return False
            
        message = """
🧪 **Тестовое напоминание**

Это тестовое сообщение для проверки работы напоминаний.

Если вы получили это сообщение, значит напоминания работают корректно!

🔔 **Напоминания приходят:**
• 🌅 9:00 - Завтрак
• ☀️ 14:00 - Обед  
• 🌙 19:00 - Ужин

Напоминания приходят только если вы еще не добавили прием пищи в этот день.
        """
        
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode='Markdown'
        )
        
        logger.info(f"Test reminder sent to user {telegram_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending test reminder to {telegram_id}: {e}")
        return False
