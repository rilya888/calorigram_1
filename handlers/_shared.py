# Auto-generated shared module extracted from bot_functions.py
# Contains imports, constants, classes, and helper functions.
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import BOT_TOKEN, ADMIN_IDS
from api_client import api_client
from database import (
    get_user_by_telegram_id, create_user_with_goal, delete_user_by_telegram_id,
    add_meal, get_daily_calories, get_meal_statistics, get_daily_meals_by_type, 
    is_meal_already_added, get_weekly_meals_by_type, delete_today_meals, delete_all_user_meals,
    get_all_users_for_broadcast, get_all_users_for_admin, get_user_count, get_meals_count, 
    get_recent_meals, get_daily_stats, check_user_subscription, activate_premium_subscription, 
    get_daily_calorie_checks_count, add_calorie_check, reset_daily_calorie_checks,
    get_user_registration_history, create_user_registration_history, mark_trial_as_used
)
from constants import (
    ADMIN_CALLBACKS, SUBSCRIPTION_DESCRIPTIONS
)
from logging_config import get_logger
import re

# Прямые импорты функций из модулей
from handlers.registration import (
    validate_user_input,
    validate_age,
    validate_height,
    validate_weight,
    check_user_registration,
    calculate_daily_calories,
    calculate_target_calories,
)

from handlers.subscription import (
    subscription_command,
    check_subscription_access,
    get_subscription_message,
)

from handlers.menu import (
    start_command,
    help_command,
    terms_command,
    show_main_menu,
    get_main_menu_keyboard,
    get_main_menu_keyboard_for_user,
    get_analysis_result_keyboard,
    handle_back_to_main,
)

from handlers.misc import (
    reset_command,
)

from services.food_analysis_service import (
    extract_weight_from_description,
    extract_calories_from_analysis,
    extract_macros_from_analysis,
    extract_dish_name_from_analysis,
    is_valid_analysis,
    clean_markdown_text,
    remove_explanations_from_analysis,
    analyze_food_photo,
    analyze_food_text,
    analyze_food_supplement,
)

# Логирование уже настроено в main.py
logger = get_logger(__name__)

# Прямые импорты функций без дублирования

def extract_calories_per_100g_from_analysis(analysis_text: str) -> Optional[int]:
    """Извлекает калорийность на 100г из текста анализа"""
    try:
        if not analysis_text or not isinstance(analysis_text, str):
            return None
            
        # Ищем паттерны калорийности на 100г
        patterns = [
            r'(\d+)\s*ккал/100г',
            r'(\d+)\s*ккал/100\s*г',
            r'(\d+)\s*ккал\s*на\s*100\s*г',
            r'(\d+)\s*ккал\s*на\s*100г',
            r'калорийность\s*на\s*100г:\s*(\d+)',
            r'калорийность\s*на\s*100\s*г:\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                calories = int(match.group(1))
                if 10 <= calories <= 1000:  # Разумные пределы для калорийности на 100г
                    logger.info(f"Extracted calories per 100g: {calories} from pattern: {pattern}")
                    return calories
        
        return None
    except Exception as e:
        logger.warning(f"Error extracting calories per 100g: {e}")
        return None

# Функции извлечения данных из анализа - используем прямые импорты

def parse_quantity_from_description(description: str) -> Tuple[float, str]:
    """Парсит количество и единицу измерения из описания блюда"""
    try:
        description = description.lower().strip()
        
        # Паттерны для поиска количества и единиц измерения
        patterns = [
            # Килограммы
            (r'(\d+(?:\.\d+)?)\s*кг', lambda x: float(x) * 1000, 'г'),
            (r'(\d+(?:\.\d+)?)\s*килограмм', lambda x: float(x) * 1000, 'г'),
            (r'(\d+(?:\.\d+)?)\s*kg', lambda x: float(x) * 1000, 'г'),
            
            # Граммы
            (r'(\d+(?:\.\d+)?)\s*г', lambda x: float(x), 'г'),
            (r'(\d+(?:\.\d+)?)\s*грамм', lambda x: float(x), 'г'),
            (r'(\d+(?:\.\d+)?)\s*g', lambda x: float(x), 'г'),
            
            # Литры
            (r'(\d+(?:\.\d+)?)\s*л', lambda x: float(x) * 1000, 'мл'),
            (r'(\d+(?:\.\d+)?)\s*литр', lambda x: float(x) * 1000, 'мл'),
            (r'(\d+(?:\.\d+)?)\s*l', lambda x: float(x) * 1000, 'мл'),
            
            # Миллилитры
            (r'(\d+(?:\.\d+)?)\s*мл', lambda x: float(x), 'мл'),
            (r'(\d+(?:\.\d+)?)\s*миллилитр', lambda x: float(x), 'мл'),
            (r'(\d+(?:\.\d+)?)\s*ml', lambda x: float(x), 'мл'),
            
            # Штуки (приблизительно по 100г)
            (r'(\d+)\s*шт', lambda x: float(x) * 100, 'г'),
            (r'(\d+)\s*штук', lambda x: float(x) * 100, 'г'),
            (r'(\d+)\s*штуки', lambda x: float(x) * 100, 'г'),
            (r'(\d+)\s*pc', lambda x: float(x) * 100, 'г'),
            
            # Порции (приблизительно 200г)
            (r'(\d+)\s*порц', lambda x: float(x) * 200, 'г'),
            (r'(\d+)\s*порции', lambda x: float(x) * 200, 'г'),
            (r'(\d+)\s*порция', lambda x: float(x) * 200, 'г'),
            
            # Стаканы (приблизительно 250г)
            (r'(\d+)\s*стакан', lambda x: float(x) * 250, 'г'),
            (r'(\d+)\s*стакана', lambda x: float(x) * 250, 'г'),
            (r'(\d+)\s*стаканов', lambda x: float(x) * 250, 'г'),
            
            # Ложки столовые (приблизительно 15г)
            (r'(\d+)\s*ст\.\s*л\.', lambda x: float(x) * 15, 'г'),
            (r'(\d+)\s*столовых ложек', lambda x: float(x) * 15, 'г'),
            (r'(\d+)\s*столовые ложки', lambda x: float(x) * 15, 'г'),
            
            # Ложки чайные (приблизительно 5г)
            (r'(\d+)\s*ч\.\s*л\.', lambda x: float(x) * 5, 'г'),
            (r'(\d+)\s*чайных ложек', lambda x: float(x) * 5, 'г'),
            (r'(\d+)\s*чайные ложки', lambda x: float(x) * 5, 'г'),
        ]
        
        for pattern, converter, unit in patterns:
            match = re.search(pattern, description)
            if match:
                quantity = converter(match.group(1))
                logger.info(f"Parsed quantity: {quantity}{unit} from '{description}'")
                return quantity, unit
        
        # Если не нашли количество, возвращаем стандартную порцию
        logger.info(f"No quantity found in '{description}', using default 100g")
        return 100.0, 'г'
        
    except Exception as e:
        logger.error(f"Error parsing quantity from description '{description}': {e}")
        return 100.0, 'г'

# Валидация и очистка текста - используем прямые импорты

# Функции админки будут импортироваться напрямую из handlers.admin

def check_subscription_access(telegram_id: int) -> dict:
    """Проверяет доступ пользователя к функциям бота"""
    return check_subscription_access_from_handler(telegram_id)

def get_subscription_message(access_info: dict) -> str:
    """Возвращает сообщение о статусе подписки"""
    return get_subscription_message_from_handler(access_info)

# Функции валидации - используем прямые импорты


# Функции клавиатур - используем прямые импорты

# Используем функции из модуля меню








# Функции расчета калорий - используем прямые импорты


























# ==================== АДМИН ФУНКЦИИ ====================





async def send_broadcast_message(bot, message_text: str, admin_id: int) -> dict:
    """Отправляет рассылку всем пользователям"""
    users = get_all_users_for_broadcast()
    total_users = len(users)
    sent_count = 0
    failed_count = 0
    blocked_count = 0
    
    # Отправляем сообщение админу о начале рассылки
    try:
        await bot.send_message(
            admin_id,
            f"📢 **Начинаем рассылку...**\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"📝 Сообщение отправляется...",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send start message to admin: {e}")
    
    for telegram_id, name in users:
        try:
            await bot.send_message(
                telegram_id,
                f"📢 **Рассылка от Calorigram**\n\n{message_text}",
                parse_mode='Markdown'
            )
            sent_count += 1
            logger.info(f"Broadcast sent to {telegram_id} ({name})")
            
            # Небольшая задержка между сообщениями
            await asyncio.sleep(0.1)
            
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to send broadcast to {telegram_id}: {e}")
            
            # Проверяем, заблокировал ли пользователь бота
            if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                blocked_count += 1
    
    # Отправляем статистику админу
    try:
        await bot.send_message(
            admin_id,
            f"✅ **Рассылка завершена!**\n\n"
            f"📊 **Статистика:**\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"✅ Успешно отправлено: {sent_count}\n"
            f"❌ Ошибок: {failed_count}\n"
            f"🚫 Заблокировали бота: {blocked_count}\n"
            f"📈 Процент доставки: {(sent_count/total_users*100):.1f}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Обратно в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
            ]),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send stats to admin: {e}")
    
    return {
        'total_users': total_users,
        'sent_count': sent_count,
        'failed_count': failed_count,
        'blocked_count': blocked_count
    }







# ==================== ФУНКЦИИ УПРАВЛЕНИЯ ПОДПИСКАМИ ====================









# ==================== ФУНКЦИИ "УЗНАТЬ КАЛОРИИ" (БЕЗ СОХРАНЕНИЯ) ====================





# Функции анализа еды - используем прямые импорты

async def transcribe_voice(audio_data: bytes):
    """Распознает речь из аудиофайла с помощью API"""
    try:
        # Валидация входных данных
        if not audio_data:
            logger.error("Invalid audio data provided - data is None or empty")
            return None
            
        if not isinstance(audio_data, bytes):
            logger.error(f"Invalid audio data type: {type(audio_data)}, expected bytes")
            return None
        
        logger.info(f"Audio data validation passed: {len(audio_data)} bytes")
        
        if len(audio_data) < 1000:  # Минимальный размер аудио
            logger.error(f"Audio data too small: {len(audio_data)} bytes (minimum: 1000)")
            return None
            
        logger.info("Starting voice transcription...")
        
        async with api_client:
            result = await api_client.analyze_voice(None, None, audio_data)
            
            if result:
                logger.info(f"Voice transcription successful, result length: {len(result)}")
                return result.strip()
            else:
                logger.error("Voice transcription failed - no result returned")
                return None
                
    except Exception as e:
        logger.error(f"Error in voice transcription: {e}")
        return None
















# ==================== ФУНКЦИИ ДЛЯ ОПЛАТЫ ПОДПИСКИ ====================



async def activate_test_subscription(user_id: int, subscription_type: str, query: Any):
    """Активирует тестовую подписку без оплаты"""
    try:
        # Определяем количество дней для тестовой подписки
        days_map = {
            'test_1_day': 1,
            'test_7_days': 7,
            'test_30_days': 30,
            'test_90_days': 90,
            'test_365_days': 365
        }
        
        days = days_map.get(subscription_type, 1)
        description = SUBSCRIPTION_DESCRIPTIONS[subscription_type]
        
        # Активируем тестовую подписку
        activate_premium_subscription(user_id, days)
        
        await query.edit_message_text(
            f"🎉 **{description} активирована!**\n\n"
            f"✅ Вы получили {days} дней бесплатного доступа ко всем функциям\n"
            f"⏰ Подписка истекает через {days} дней\n\n"
            f"🧪 **Это тестовая подписка** - никаких реальных денег не списывалось\n\n"
            f"💡 Для продления используйте /profile",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 К профилю", callback_data="profile")]
            ]),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error activating test subscription: {e}")
        await query.edit_message_text("❌ Ошибка при активации тестовой подписки.")

async def activate_trial_subscription(user_id: int, query: Any):
    """Активирует бесплатный триал"""
    try:
        # Активируем триал на 1 день
        activate_premium_subscription(user_id, 1)
        
        await query.edit_message_text(
            "🎉 **Триальный период активирован!**\n\n"
            "✅ Вы получили 1 день бесплатного доступа ко всем функциям\n"
            "⏰ Подписка истекает завтра в это же время\n\n"
            "💡 Для продления используйте /profile",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 К профилю", callback_data="profile")]
            ]),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error activating trial subscription: {e}")
        await query.edit_message_text(
            "❌ Ошибка активации триала. Попробуйте позже."
        )

async def create_payment_invoice(user_id: int, subscription_type: str, price: int, query: Any, context: ContextTypes.DEFAULT_TYPE):
    """Создает инвойс для оплаты через Telegram Stars"""
    try:
        # Проверяем лимиты согласно новой документации
        if price > 10000:  # Максимум 10,000 Stars согласно Bot API 9.0+
            await query.message.reply_text(
                "❌ **Ошибка:** Слишком высокая цена!\n\n"
                "Максимальная цена подписки: 10,000 ⭐\n"
                "Пожалуйста, выберите другой вариант подписки.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К выбору подписки", callback_data="buy_subscription")]
                ]),
                parse_mode='Markdown'
            )
            return
        
        if price < 1:  # Минимум 1 Star
            await query.message.reply_text(
                "❌ **Ошибка:** Слишком низкая цена!\n\n"
                "Минимальная цена подписки: 1 ⭐",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К выбору подписки", callback_data="buy_subscription")]
                ]),
                parse_mode='Markdown'
            )
            return
        
        # Определяем количество дней подписки
        days_map = {
            'premium_7_days': 7
        }
        
        days = days_map.get(subscription_type, 30)
        description = SUBSCRIPTION_DESCRIPTIONS[subscription_type]
        
        # Убираем информацию о балансе из описания инвойса
        balance_info = ""
        
        # Сохраняем данные о покупке в контексте
        context.user_data['pending_payment'] = {
            'subscription_type': subscription_type,
            'price': price,
            'days': days,
            'user_id': user_id
        }
        
        # Создаем инвойс для оплаты
        from telegram import LabeledPrice
        
        # Создаем инвойс с правильными параметрами для Telegram Stars
        invoice_title = f"Подписка Calorigram - {description}"
        
        invoice_description = f"Премиум доступ к боту Calorigram на {days} дней{balance_info}"
        
        await query.message.reply_invoice(
            title=invoice_title,
            description=invoice_description,
            payload=f"subscription_{subscription_type}",
            provider_token="",  # Для Telegram Stars не нужен provider_token
            currency="XTR",  # Telegram Stars currency
            prices=[LabeledPrice(f"Подписка на {days} дней", price)]  # Цена в Stars (без умножения на 100)
        )
        
        # Логируем создание инвойса
        logger.info(f"Created invoice: user {user_id}, subscription {subscription_type}, {price} Stars, {days} days")
        
    except Exception as e:
        logger.error(f"Error creating payment invoice: {e}")
        await query.message.reply_text(
            "❌ Ошибка создания платежа. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 К выбору подписки", callback_data="buy_subscription")]
            ])
        )



async def get_bot_star_balance():
    """Получает текущий баланс Stars бота"""
    try:
        # Временно возвращаем None, так как метод get_my_star_balance() 
        # пока не реализован в python-telegram-bot
        # NOTE: Метод будет реализован в будущих версиях библиотеки
        return None
    except Exception as e:
        logger.error(f"Error getting bot star balance: {e}")
        return None









# Новые функции для подтверждения анализа фото












