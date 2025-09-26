import asyncio
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import BOT_TOKEN, TEST_MODE, ADMIN_IDS
from api_client import APIClient, api_client
from database import (get_db_connection, get_user_by_telegram_id, create_user_with_goal, delete_user_by_telegram_id,
                     add_meal, get_daily_calories, get_meal_statistics, get_daily_meals_by_type, is_meal_already_added, get_weekly_meals_by_type, delete_today_meals, delete_all_user_meals,
                     get_all_users_for_broadcast, get_all_users_for_admin, get_user_count, get_meals_count, get_recent_meals, get_daily_stats,
                     check_user_subscription, activate_premium_subscription, get_daily_calorie_checks_count, add_calorie_check, reset_daily_calorie_checks,
                     get_user_registration_history, create_user_registration_history, mark_trial_as_used)
from constants import (
    MIN_AGE, MAX_AGE, MIN_HEIGHT, MAX_HEIGHT, MIN_WEIGHT, MAX_WEIGHT,
    ERROR_MESSAGES, ACTIVITY_LEVELS, GENDERS,
    ADMIN_CALLBACKS, SUBSCRIPTION_PRICES, SUBSCRIPTION_DESCRIPTIONS,
    GOALS, GOAL_MULTIPLIERS
)
from utils import validate_telegram_id
from logging_config import get_logger
import re

# Логирование уже настроено в main.py
logger = get_logger(__name__)

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
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Error validating user input: {e}")
        return False, "Ошибка валидации данных"
    except Exception as e:
        logger.error(f"Unexpected error validating user input: {e}")
        return False, "Ошибка валидации данных"

def extract_weight_from_description(description: str) -> Optional[float]:
    """Извлекает вес из описания блюда"""
    try:
        # Ищем паттерны веса в описании
        weight_patterns = [
            r'(\d+(?:\.\d+)?)\s*кг',
            r'(\d+(?:\.\d+)?)\s*г',
            r'(\d+(?:\.\d+)?)\s*грамм',
            r'(\d+(?:\.\d+)?)\s*граммов'
        ]
        
        for pattern in weight_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                weight = float(match.group(1))
                if 'кг' in pattern:
                    return weight * 1000  # Конвертируем кг в граммы
                else:
                    return weight
        
        return None
    except Exception as e:
        logger.warning(f"Error extracting weight from description: {e}")
        return None

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

def extract_calories_from_analysis(analysis_text: str) -> Optional[int]:
    """Извлекает общую калорийность блюда из текста анализа"""
    try:
        if not analysis_text or not isinstance(analysis_text, str):
            logger.warning("Invalid analysis text provided")
            return None
            
        logger.info(f"Extracting calories from analysis text: {analysis_text[:300]}...")
            
        # Ищем паттерны для общей калорийности (не на 100г)
        patterns = [
            r'Общая калорийность:\s*(\d+)\s*ккал',
            r'Общее количество калорий:\s*(\d+)\s*ккал',
            r'Калорийность блюда:\s*(\d+)\s*ккал',
            r'Калорийность:\s*(\d+)\s*ккал\s*$',  # В конце строки
            r'(\d+)\s*ккал\s*$',  # Просто число ккал в конце
            r'калорийность:\s*(\d+)',
            r'калорий:\s*(\d+)',
            # Добавляем паттерны для калорийности с указанием веса
            r'(\d+)\s*ккал\s*на\s*(\d+)\s*г',  # калории на грамм
            r'(\d+)\s*ккал\s*на\s*(\d+)\s*кг',  # калории на килограмм
            r'(\d+)\s*ккал/100г',  # калории на 100г
            r'(\d+)\s*ккал/100\s*г',  # калории на 100 г
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, analysis_text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    if i >= 7:  # Паттерны с указанием веса (индексы 7-10)
                        calories_per_unit = int(match.group(1))
                        weight = int(match.group(2))
                        
                        # Вычисляем общую калорийность
                        if 'кг' in pattern:
                            # Если вес в кг, умножаем на 1000 для перевода в граммы
                            total_calories = calories_per_unit * weight * 10  # на 100г
                        else:
                            # Если вес в граммах
                            total_calories = calories_per_unit * weight / 100  # на 100г
                        
                        total_calories = int(total_calories)
                        
                        # Проверяем разумность значения
                        if 10 <= total_calories <= 50000:
                            logger.info(f"Extracted calories: {total_calories} from pattern: {pattern} (calculated from {calories_per_unit} ккал/100г for {weight}г)")
                            return total_calories
                    else:
                        # Обычные паттерны
                        calories = int(match.group(1))
                        # Проверяем разумность значения (от 10 до 50000 калорий для больших порций)
                        if 10 <= calories <= 50000:
                            logger.info(f"Extracted calories: {calories} from pattern: {pattern}")
                            return calories
                except ValueError:
                    logger.warning(f"Invalid calories value: {match.group(1)}")
                    continue
        
        # Если не нашли общую калорийность, ищем любую калорийность
        fallback_patterns = [
            r'(\d+)\s*ккал',
            r'калорийность:\s*(\d+)',
            r'калорий:\s*(\d+)'
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                try:
                    calories = int(match.group(1))
                    if 10 <= calories <= 50000:
                        logger.info(f"Extracted calories (fallback): {calories} from pattern: {pattern}")
                        return calories
                except ValueError:
                    logger.warning(f"Invalid calories value (fallback): {match.group(1)}")
                    continue
        
        logger.warning("No calories found in analysis text")
        return None
    except Exception as e:
        logger.error(f"Error extracting calories from analysis: {e}")
        return None

def extract_dish_name_from_analysis(analysis_text: str) -> Optional[str]:
    """Извлекает название блюда из текста анализа"""
    try:
        # Ищем паттерн "Название: [название]"
        pattern = r'Название:\s*([^\n]+)'
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    except Exception as e:
        logger.error(f"Error extracting dish name from analysis: {e}")
        return None

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

def is_valid_analysis(analysis_text: str) -> bool:
    """Проверяет, является ли анализ валидным (содержит калории)"""
    calories = extract_calories_from_analysis(analysis_text)
    return calories is not None and calories > 0

def clean_markdown_text(text: str) -> str:
    """Очищает текст от проблемных символов Markdown для Telegram"""
    try:
        # Экранируем проблемные символы
        text = text.replace('*', '\\*')
        text = text.replace('_', '\\_')
        text = text.replace('[', '\\[')
        text = text.replace(']', '\\]')
        text = text.replace('`', '\\`')
        text = text.replace('~', '\\~')
        text = text.replace('>', '\\>')
        text = text.replace('#', '\\#')
        text = text.replace('+', '\\+')
        text = text.replace('-', '\\-')
        text = text.replace('=', '\\=')
        text = text.replace('|', '\\|')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        text = text.replace('.', '\\.')
        text = text.replace('!', '\\!')
        return text
    except Exception as e:
        logger.error(f"Error cleaning markdown text: {e}")
        return text

def remove_explanations_from_analysis(text: str) -> str:
    """Удаляет пояснения и дополнительные расчеты из анализа ИИ"""
    try:
        # Ищем раздел "Пояснение расчетов" и обрезаем его
        explanation_patterns = [
            r'### Пояснение расчетов:.*$',
            r'## Пояснение расчетов:.*$',
            r'# Пояснение расчетов:.*$',
            r'Пояснение расчетов:.*$',
            r'Таким образом.*$',
            r'Итак.*$',
            r'В итоге.*$',
            r'Итого.*$'
        ]
        
        for pattern in explanation_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Убираем лишние переносы строк в конце
        text = text.rstrip('\n')
        
        return text
    except Exception as e:
        logger.error(f"Error removing explanations from analysis: {e}")
        return text

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return user_id in ADMIN_IDS

def check_subscription_access(telegram_id: int) -> dict:
    """Проверяет доступ пользователя к функциям бота"""
    try:
        subscription = check_user_subscription(telegram_id)
        
        if subscription['is_active']:
            return {
                'has_access': True,
                'subscription_type': subscription['type'],
                'expires_at': subscription['expires_at']
            }
        else:
            return {
                'has_access': False,
                'subscription_type': subscription['type'],
                'expires_at': subscription['expires_at']
            }
    except Exception as e:
        logger.error(f"Error checking subscription access: {e}")
        return {'has_access': False, 'subscription_type': 'error', 'expires_at': None}

def get_subscription_message(access_info: dict) -> str:
    """Возвращает сообщение о статусе подписки"""
    if access_info['has_access']:
        if access_info['subscription_type'] == 'trial':
            return f"🆓 **Триальный период**\n\nДоступен до: {access_info['expires_at']}\n\nПосле истечения триального периода потребуется подписка для продолжения использования бота."
        elif access_info['subscription_type'] == 'premium':
            return f"⭐ **Премиум подписка**\n\nДействует до: {access_info['expires_at'] or 'Бессрочно'}\n\nСпасибо за поддержку!"
    else:
        if access_info['subscription_type'] == 'trial_expired':
            return "❌ **Триальный период истек**\n\nДля продолжения использования бота необходимо оформить подписку.\n\n🌟 **Оплата через Telegram Stars:**\n• 7 дней - 10 ⭐\n\n💎 Безопасно • Мгновенно • Без комиссий"
        elif access_info['subscription_type'] == 'trial_used':
            return "❌ **Триальный период уже был использован**\n\nВы уже использовали бесплатный триальный период. Для продолжения использования бота необходимо оформить подписку.\n\n🌟 **Оплата через Telegram Stars:**\n• 7 дней - 10 ⭐\n\n💎 Безопасно • Мгновенно • Без комиссий"
        else:
            return "❌ **Нет активной подписки**\n\nДля использования бота необходимо оформить подписку.\n\n🌟 **Оплата через Telegram Stars:**\n• 7 дней - 10 ⭐\n\n💎 Безопасно • Мгновенно • Без комиссий"

def validate_age(age: str) -> Optional[int]:
    """Валидация возраста"""
    try:
        age_int = int(age)
        if MIN_AGE <= age_int <= MAX_AGE:
            return age_int
        return None
    except ValueError:
        return None

def validate_height(height: str) -> Optional[float]:
    """Валидация роста"""
    try:
        height_float = float(height)
        if MIN_HEIGHT <= height_float <= MAX_HEIGHT:
            return height_float
        return None
    except ValueError:
        return None

def validate_weight(weight: str) -> Optional[float]:
    """Валидация веса"""
    try:
        weight_float = float(weight)
        if MIN_WEIGHT <= weight_float <= MAX_WEIGHT:
            return weight_float
        return None
    except ValueError:
        return None

def check_user_registration(user_id: int) -> Optional[Tuple[Any, ...]]:
    """Проверяет, зарегистрирован ли пользователь"""
    return get_user_by_telegram_id(user_id)

async def send_not_registered_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет сообщение о том, что пользователь не зарегистрирован"""
    message = ERROR_MESSAGES['user_not_registered']
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(message)
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(message)

def get_main_menu_keyboard(user_id: Optional[int] = None):
    """Создает клавиатуру главного меню"""
    keyboard = [
        [InlineKeyboardButton("🍽️ Добавить блюдо", callback_data="add_dish")],
        [InlineKeyboardButton("🔍 Узнать калории", callback_data="check_calories")],
        [InlineKeyboardButton("📊 Статистика", callback_data="statistics")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    
    # Добавляем кнопку подписки только если пользователь не имеет активной подписки
    if user_id:
        subscription = check_user_subscription(user_id)
        if not subscription['is_active'] or subscription['type'] == 'trial':
            keyboard.insert(3, [InlineKeyboardButton("⭐ Купить подписку", callback_data="subscription")])
        keyboard.insert(4, [InlineKeyboardButton("📋 Условия подписки", callback_data="terms")])
    else:
        # Если user_id не передан, показываем кнопку "Купить подписку" по умолчанию
        keyboard.insert(3, [InlineKeyboardButton("⭐ Купить подписку", callback_data="subscription")])
        keyboard.insert(4, [InlineKeyboardButton("📋 Условия подписки", callback_data="terms")])
    
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard_for_user(update: Update):
    """Создает клавиатуру главного меню для конкретного пользователя"""
    user_id = update.effective_user.id
    return get_main_menu_keyboard(user_id)

def get_analysis_result_keyboard():
    """Создает клавиатуру для результата анализа с кнопкой Меню"""
    keyboard = [
        [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню для зарегистрированных пользователей"""
    try:
        if hasattr(update, 'message') and update.message:
            # Если это команда (например, /start)
            await update.message.reply_text(
                "🏠 **Главное меню**\n\n"
                "Выберите нужную функцию:",
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
        else:
            # Если это callback query
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                "🏠 **Главное меню**\n\n"
                "Выберите нужную функцию:",
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error showing main menu: {e}")
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text("❌ Ошибка при загрузке главного меню.")
        else:
            query = update.callback_query
            await query.edit_message_text("❌ Ошибка при загрузке главного меню.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user.id,))
            user_data = cursor.fetchone()
        
        if user_data:
            # Пользователь зарегистрирован - показываем главное меню
            await show_main_menu(update, context)
        else:
            # Пользователь не зарегистрирован - предлагаем регистрацию
            welcome_message = f"""
Привет, {user.first_name}! 👋

Добро пожаловать в Calorigram - бот для подсчета калорий!

Я помогу тебе:
• Рассчитать суточную норму калорий
• Отслеживать твой прогресс
• Давать рекомендации по питанию

Для начала работы нужно зарегистрироваться:
            """
            
            keyboard = [
                [InlineKeyboardButton("📝 Регистрация", callback_data="register")],
                [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_message, reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при проверке регистрации. Попробуйте позже."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📋 Доступные команды:

/start - Начать работу с ботом
/register - Регистрация в системе
/profile - Посмотреть профиль
/add - Добавить блюдо
/addmeal - Анализ блюда (фото/текст/голос)
/addphoto - Анализ фото еды ИИ
/addtext - Анализ описания блюда ИИ
/addvoice - Анализ голосового описания ИИ
/terms - Условия подписки
/reset - Удалить все данные регистрации
/help - Показать эту справку

🔧 Функции бота:
• Расчет суточной нормы калорий
• Отслеживание прогресса
• Рекомендации по питанию
• Добавление блюд по приемам пищи
• Анализ фотографий еды с помощью ИИ
• Анализ текстового описания блюд
• Анализ голосовых сообщений
• Безопасное удаление данных
    """
    
    # Проверяем, это команда или callback запрос
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(help_text, reply_markup=get_main_menu_keyboard_for_user(update))
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(help_text, reply_markup=get_main_menu_keyboard_for_user(update))

async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /terms - условия подписки"""
    terms_text = """
📋 **Условия подписки Calorigram Bot**

**🆓 БЕСПЛАТНЫЙ ПЛАН:**
• До 5 анализов еды в день
• Базовые напоминания о приемах пищи
• Профиль пользователя
• Статистика за текущий день

**💎 ПРЕМИУМ ПОДПИСКА:**
• ✅ **Безлимитный анализ еды** - сколько угодно анализов в день
• ✅ **Расширенная статистика** - детальная аналитика по неделям и месяцам
• ✅ **Персональные рекомендации** - советы по питанию на основе ваших данных
• ✅ **Экспорт данных** - возможность скачать вашу статистику
• ✅ **Приоритетная поддержка** - быстрые ответы на вопросы
• ✅ **Дополнительные напоминания** - настройка времени и частоты
• ✅ **История анализов** - доступ ко всем предыдущим анализам
• ✅ **Детальные отчеты** - подробная разбивка по БЖУ и калориям

**💰 СТОИМОСТЬ ПОДПИСКИ:**
• Месячная подписка: 299 рублей
• Годовая подписка: 2990 рублей (экономия 20%)

**🔄 ОТМЕНА ПОДПИСКИ:**
• Подписку можно отменить в любое время
• Доступ к премиум функциям сохраняется до конца оплаченного периода
• Возврат средств не предусмотрен

**📱 СПОСОБЫ ОПЛАТЫ:**
• Telegram Stars (рекомендуется)
• Банковские карты
• Apple Pay / Google Pay

**🛡️ ГАРАНТИИ:**
• Безопасная обработка платежей
• Защита персональных данных
• Стабильная работа сервиса 24/7

**📞 ПОДДЕРЖКА:**
При возникновении вопросов обращайтесь к администратору: @your_support_username

**📅 ДАТА ОБНОВЛЕНИЯ:** 19.09.2024
    """
    
    # Проверяем, это команда или callback запрос
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(terms_text, reply_markup=get_main_menu_keyboard_for_user(update), parse_mode='Markdown')
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(terms_text, reply_markup=get_main_menu_keyboard_for_user(update), parse_mode='Markdown')

async def subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /subscription"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        user_data = check_user_registration(user.id)
        if not user_data:
            # Проверяем, это команда или callback запрос
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(
                    "❌ Вы не зарегистрированы в системе!\n"
                    "Используйте /register для регистрации.",
                    reply_markup=get_main_menu_keyboard()
                )
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(
                    "❌ Вы не зарегистрированы в системе!\n"
                    "Используйте /register для регистрации.",
                    reply_markup=get_main_menu_keyboard()
                )
            return
        
        # Получаем информацию о подписке
        access_info = check_subscription_access(user.id)
        subscription_msg = get_subscription_message(access_info)
        
        # Проверяем, это команда или callback запрос
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                subscription_msg,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                subscription_msg,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error in subscription_command: {e}")
        # Проверяем, это команда или callback запрос
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                "❌ Произошла ошибка при проверке подписки. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ Произошла ошибка при проверке подписки. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /register"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if existing_user:
            await update.message.reply_text("Вы уже зарегистрированы! Используйте /profile для просмотра данных.")
            return
        
        # Сохраняем состояние регистрации
        context.user_data['registration_step'] = 'name'
        context.user_data['user_data'] = {'telegram_id': user.id}
        
        await update.message.reply_text(
            "Давайте зарегистрируем вас в системе!\n\n"
            "Введите ваше имя:"
        )
    except Exception as e:
        logger.error(f"Error in register_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при проверке регистрации. Попробуйте позже."
        )

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений для регистрации и анализа блюд"""
    # Проверяем, ожидается ли ввод Telegram ID для админки
    if context.user_data.get('admin_waiting_for_telegram_id', False):
        await handle_admin_telegram_id_input(update, context)
        return
    
    # Проверяем, ожидается ли текстовое описание блюда
    if (context.user_data.get('waiting_for_text', False) or 
        context.user_data.get('waiting_for_check_text', False) or
        context.user_data.get('waiting_for_text_after_photo', False) or
        context.user_data.get('waiting_for_check_text_after_photo', False)):
        await handle_food_text_analysis(update, context)
        return
    
    # Проверяем, ожидается ли текст рассылки
    if context.user_data.get('waiting_for_broadcast_text', False):
        await handle_broadcast_text_input(update, context)
        return
    
    # Обработка регистрации
    if 'registration_step' not in context.user_data:
        await update.message.reply_text("Используйте /start для начала работы с ботом")
        return
    
    text = update.message.text
    step = context.user_data['registration_step']
    user_data = context.user_data['user_data']
    
    if step == 'name':
        user_data['name'] = text
        context.user_data['registration_step'] = 'gender'
        
        keyboard = [
            [InlineKeyboardButton("👨 Мужской", callback_data="gender_male")],
            [InlineKeyboardButton("👩 Женский", callback_data="gender_female")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите ваш пол:",
            reply_markup=reply_markup
        )
        
    elif step == 'age':
        age = validate_age(text)
        if age is None:
            await update.message.reply_text(f"Пожалуйста, введите корректный возраст ({MIN_AGE}-{MAX_AGE}):")
            return
        user_data['age'] = age
        context.user_data['registration_step'] = 'height'
        await update.message.reply_text("Введите ваш рост в см:")
            
    elif step == 'height':
        height = validate_height(text)
        if height is None:
            await update.message.reply_text(f"Пожалуйста, введите корректный рост ({MIN_HEIGHT}-{MAX_HEIGHT} см):")
            return
        user_data['height'] = height
        context.user_data['registration_step'] = 'weight'
        await update.message.reply_text("Введите ваш вес в кг:")
            
    elif step == 'weight':
        weight = validate_weight(text)
        if weight is None:
            await update.message.reply_text(f"Пожалуйста, введите корректный вес ({MIN_WEIGHT}-{MAX_WEIGHT} кг):")
            return
        user_data['weight'] = weight
        context.user_data['registration_step'] = 'activity'
        
        keyboard = [
            [InlineKeyboardButton("🛌 Минимальная", callback_data="activity_minimal")],
            [InlineKeyboardButton("🏃 Легкая", callback_data="activity_light")],
            [InlineKeyboardButton("💪 Умеренная", callback_data="activity_moderate")],
            [InlineKeyboardButton("🔥 Высокая", callback_data="activity_high")],
            [InlineKeyboardButton("⚡ Очень высокая", callback_data="activity_very_high")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите ваш уровень активности:",
            reply_markup=reply_markup
        )

async def handle_activity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора уровня активности"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('activity_'):
        # Проверяем, есть ли данные пользователя
        if 'user_data' not in context.user_data:
            await query.message.reply_text(
                "❌ Ошибка: данные регистрации не найдены.\n"
                "Пожалуйста, начните регистрацию заново с помощью /register"
            )
            return
            
        activity_levels = {
            'activity_minimal': 'Минимальная',
            'activity_light': 'Легкая',
            'activity_moderate': 'Умеренная',
            'activity_high': 'Высокая',
            'activity_very_high': 'Очень высокая'
        }
        
        user_data = context.user_data['user_data']
        user_data['activity_level'] = activity_levels[query.data]
        
        # Переходим к выбору цели
        context.user_data['registration_step'] = 'goal'
        
        keyboard = [
            [InlineKeyboardButton("📉 Похудеть", callback_data="goal_lose_weight")],
            [InlineKeyboardButton("⚖️ Держать себя в форме", callback_data="goal_maintain")],
            [InlineKeyboardButton("📈 Набрать вес", callback_data="goal_gain_weight")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎯 **Выберите вашу цель:**\n\n"
            "• **Похудеть** - снижение веса\n"
            "• **Держать себя в форме** - поддержание текущего веса\n"
            "• **Набрать вес** - увеличение веса",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def calculate_daily_calories(age, height, weight, gender: str, activity_level: str) -> int:
    """Рассчитывает суточную норму калорий по формуле Миффлин-Сен Жеор"""
    try:
        # Преобразуем данные в нужные типы
        age = int(age)
        height = float(height)
        weight = float(weight)
        
        logger.info(f"Calculating calories for: age={age}, height={height}, weight={weight}, gender={gender}, activity={activity_level}")
        
        # Формула Миффлин-Сен Жеор (более точная)
        if gender == 'Мужской':
            # BMR для мужчин = (10 * weight) + (6.25 * height) - (5 * age) + 5
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:  # Женский
            # BMR для женщин = (10 * weight) + (6.25 * height) - (5 * age) - 161
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        
        # Коэффициенты активности
        multiplier = ACTIVITY_LEVELS.get(activity_level, 1.55)
        daily_calories = int(bmr * multiplier)
        
        logger.info(f"Calculated BMR: {bmr}, multiplier: {multiplier}, daily_calories: {daily_calories}")
        
        # Проверяем разумность результата
        if daily_calories < 800 or daily_calories > 5000:
            logger.warning(f"Unusual daily calories calculated: {daily_calories} for user with age={age}, height={height}, weight={weight}, gender={gender}, activity={activity_level}")
        
        return daily_calories
        
    except Exception as e:
        logger.error(f"Error calculating daily calories: {e}, types: age={type(age)}, height={type(height)}, weight={type(weight)}")
        # Возвращаем среднее значение в случае ошибки
        return 2000

def calculate_target_calories(daily_calories: int, goal: str) -> int:
    """Рассчитывает целевую норму калорий на основе цели пользователя"""
    multiplier = GOAL_MULTIPLIERS.get(goal, 1.0)
    target_calories = int(daily_calories * multiplier)
    return target_calories

async def handle_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора цели пользователя"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, есть ли данные пользователя
    if 'user_data' not in context.user_data:
        await query.message.reply_text(
            "❌ Ошибка: данные регистрации не найдены.\n"
            "Пожалуйста, начните регистрацию заново с помощью /register"
        )
        return
    
    goal_mapping = {
        'goal_lose_weight': 'lose_weight',
        'goal_maintain': 'maintain',
        'goal_gain_weight': 'gain_weight'
    }
    
    user_data = context.user_data['user_data']
    user_data['goal'] = goal_mapping[query.data]
    
    # Получаем имя пользователя
    name = user_data.get('name', 'Пользователь')
    
    # Рассчитываем суточную норму калорий
    daily_calories = calculate_daily_calories(
        user_data['age'],
        user_data['height'],
        user_data['weight'],
        user_data['gender'],
        user_data['activity_level']
    )
    user_data['daily_calories'] = daily_calories
    
    # Рассчитываем целевую норму калорий на основе цели
    target_calories = calculate_target_calories(daily_calories, user_data['goal'])
    user_data['target_calories'] = target_calories
    
    # Сохраняем пользователя в базу данных
    success = create_user_with_goal(
        user_data['telegram_id'],
        user_data['name'],
        user_data['gender'],
        user_data['age'],
        user_data['height'],
        user_data['weight'],
        user_data['activity_level'],
        user_data['daily_calories'],
        user_data['goal'],
        user_data['target_calories']
    )
    
    if not success:
        await query.message.reply_text(
            "❌ Произошла ошибка при сохранении данных. Попробуйте регистрацию заново."
        )
        return
    
    # Очищаем данные регистрации
    context.user_data.pop('registration_step', None)
    context.user_data.pop('user_data', None)
    
    # Используем полное главное меню
    reply_markup = get_main_menu_keyboard()
    
    # Получаем информацию о подписке
    access_info = check_subscription_access(user_data['telegram_id'])
    subscription_msg = get_subscription_message(access_info)
    
    # Формируем сообщение с информацией о целях
    goal_text = GOALS[user_data['goal']]
    goal_emoji = "📉" if user_data['goal'] == 'lose_weight' else "⚖️" if user_data['goal'] == 'maintain' else "📈"
    
    await query.edit_message_text(
        f"Привет {name}, ✅ **Регистрация завершена!**\n\n"
        f"🎯 **Ваша цель:** {goal_emoji} {goal_text}\n"
        f"📊 **Расчетная норма:** {daily_calories} ккал\n"
        f"🎯 **Целевая норма:** {target_calories} ккал\n\n"
        f"{subscription_msg}\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /profile"""
    user = update.effective_user
    logger.info(f"Profile command called by user {user.id}")
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        user_data = check_user_registration(user.id)
        
        if not user_data:
            await send_not_registered_message(update, context)
            return
        
        # Получаем информацию о подписке
        subscription_info = check_user_subscription(user.id)
        logger.info(f"Subscription info for user {user.id}: {subscription_info}")
        
        # Формируем текст о подписке
        subscription_text = ""
        if subscription_info['is_active']:
            if subscription_info['type'] == 'trial':
                subscription_text = f"🆓 Триальный период\nДоступен до: {subscription_info['expires_at']}"
            elif subscription_info['type'] == 'premium':
                if subscription_info['expires_at']:
                    subscription_text = f"⭐ Премиум подписка\nДействует до: {subscription_info['expires_at']}"
                else:
                    subscription_text = "⭐ Премиум подписка\nБез ограничений"
        else:
            if subscription_info['type'] == 'trial_expired':
                subscription_text = f"❌ Триальный период истек\nИстек: {subscription_info['expires_at']}"
            elif subscription_info['type'] == 'premium_expired':
                subscription_text = f"❌ Премиум подписка истекла\nИстекла: {subscription_info['expires_at']}"
            else:
                subscription_text = "❌ Нет активной подписки"
        
        # Получаем информацию о цели и целевой норме калорий
        goal = user_data[13] if len(user_data) > 13 else 'maintain'
        target_calories = int(user_data[14]) if len(user_data) > 14 and user_data[14] else int(user_data[8])
        
        # Формируем текст о цели
        goal_text = GOALS.get(goal, 'Держать себя в форме')
        goal_emoji = "📉" if goal == 'lose_weight' else "⚖️" if goal == 'maintain' else "📈"
        
        profile_text = f"""
👤 Ваш профиль:

📝 Имя: {user_data[2]}
👤 Пол: {user_data[3]}
🎂 Возраст: {user_data[4]} лет
📏 Рост: {user_data[5]} см
⚖️ Вес: {user_data[6]} кг
🏃 Уровень активности: {user_data[7]}
🎯 Цель: {goal_emoji} {goal_text}
📊 Расчетная норма: {user_data[8]} ккал
🎯 Целевая норма: {target_calories} ккал
📅 Дата регистрации: {user_data[9]}

{subscription_text}
        """
        
        await update.message.reply_text(profile_text, reply_markup=get_main_menu_keyboard())
    except Exception as e:
        logger.error(f"Error in profile_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении данных профиля. Попробуйте позже."
        )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /reset"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if not existing_user:
            await send_not_registered_message(update, context)
            return
    except Exception as e:
        logger.error(f"Error in reset_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при проверке регистрации. Попробуйте позже."
        )
        return
    
    # Показываем предупреждение с кнопками подтверждения
    warning_text = """
⚠️ **ВНИМАНИЕ!** ⚠️

Вы собираетесь удалить ВСЕ ваши данные:
• Данные регистрации (имя, пол, возраст, рост, вес, уровень активности)
• Суточная норма калорий
• ВСЕ данные о приемах пищи за все время
• Статистика и история питания

🗑️ **УДАЛЕНИЕ БЕЗВОЗВРАТНО!**

Вы уверены, что хотите продолжить?
    """
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, удалить все данные", callback_data="reset_confirm")],
        [InlineKeyboardButton("🔙 Вернуться в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(warning_text, reply_markup=reply_markup, parse_mode='Markdown')

async def dayreset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /dayreset"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        user_data = check_user_registration(user.id)
        if not user_data:
            await update.message.reply_text(
                "❌ Вы не зарегистрированы в системе!\n"
                "Используйте /register для регистрации."
            )
            return
        
        # Удаляем все приемы пищи за сегодня
        success = delete_today_meals(user.id)
        
        if success:
            await update.message.reply_text(
                "✅ **Данные за сегодня удалены!**\n\n"
                "Все приемы пищи за сегодняшний день были удалены.\n"
                "Теперь вы можете снова добавлять завтрак, обед и ужин.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "ℹ️ **Нет данных для удаления**\n\n"
                "У вас нет записей о приемах пищи за сегодняшний день.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in dayreset command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при удалении данных. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

async def resetcounters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /resetcounters - сброс счетчиков для админов"""
    user = update.effective_user
    
    try:
        # Проверяем, является ли пользователь админом
        if user.id not in ADMIN_IDS:
            await update.message.reply_text(
                "❌ У вас нет прав для выполнения этой команды."
            )
            return
        
        # Сбрасываем счетчики
        success = reset_daily_calorie_checks()
        
        if success:
            await update.message.reply_text(
                "✅ **Счетчики сброшены!**\n\n"
                "Все пользователи снова могут использовать функцию 'Узнать калории' 3 раза в день.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Произошла ошибка при сбросе счетчиков. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Error in resetcounters command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при сбросе счетчиков. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin"""
    user = update.effective_user
    
    # Проверяем, является ли пользователь админом
    if not is_admin(user.id):
        await update.message.reply_text(
            "❌ У вас нет прав доступа к админ панели!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await show_admin_panel(update, context)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает админ панель"""
    try:
        # Получаем общую статистику
        user_count = get_user_count()
        meals_count = get_meals_count()
        daily_stats = get_daily_stats()
        
        # Получаем баланс Stars бота
        try:
            balance_stars = await get_bot_star_balance()
            if balance_stars is not None:
                balance_text = f"\n💰 **Баланс Stars:** {balance_stars} ⭐"
            else:
                balance_text = "\n💰 **Баланс Stars:** недоступен (требуется регистрация разработчика)"
        except Exception as e:
            logger.warning(f"Could not get star balance in admin panel: {e}")
            balance_text = "\n💰 **Баланс Stars:** недоступен (требуется регистрация разработчика)"
        
        # Добавляем информацию о тестовом режиме
        test_mode_text = ""
        
        admin_text = f"""
🔧 **Админ панель**

📊 **Общая статистика:**
• Всего пользователей: {user_count}
• Всего записей о еде: {meals_count}

📈 **За сегодня:**
• Активных пользователей: {daily_stats['active_users']}
• Записей о еде: {daily_stats['meals_today']}
• Общих калорий: {daily_stats['total_calories']}{balance_text}{test_mode_text}

Выберите действие:
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data=ADMIN_CALLBACKS['admin_stats'])],
            [InlineKeyboardButton("👥 Пользователи", callback_data=ADMIN_CALLBACKS['admin_users'])],
            [InlineKeyboardButton("🍽️ Последние приемы пищи", callback_data=ADMIN_CALLBACKS['admin_meals'])],
            [InlineKeyboardButton("⭐ Управление подписками", callback_data=ADMIN_CALLBACKS['admin_subscriptions'])],
            [InlineKeyboardButton("💎 Баланс Stars", callback_data="admin_star_balance")],
            [InlineKeyboardButton("📢 Рассылка", callback_data=ADMIN_CALLBACKS['admin_broadcast'])],
            [InlineKeyboardButton("🔙 Главное меню", callback_data=ADMIN_CALLBACKS['admin_back'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode='Markdown')
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error showing admin panel: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при загрузке админ панели. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /add"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if not existing_user:
            await send_not_registered_message(update, context)
            return
    except Exception as e:
        logger.error(f"Error in add_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при проверке регистрации. Попробуйте позже."
        )
        return
    
    # Создаем подменю для выбора приема пищи
    keyboard = [
        [InlineKeyboardButton("🌅 Завтрак", callback_data="addmeal")],
        [InlineKeyboardButton("☀️ Обед", callback_data="addmeal")],
        [InlineKeyboardButton("🌙 Ужин", callback_data="addmeal")],
        [InlineKeyboardButton("🍎 Перекус", callback_data="addmeal")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🍽️ **Добавить блюдо**\n\n"
        "Выберите прием пищи:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def addmeal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /addmeal"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if not existing_user:
            await send_not_registered_message(update, context)
            return
    except Exception as e:
        logger.error(f"Error in addmeal_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при проверке регистрации. Попробуйте позже."
        )
        return
    
    # Создаем подменю для анализа блюда
    keyboard = [
        [InlineKeyboardButton("📷 Анализ по фото", callback_data="analyze_photo")],
        [InlineKeyboardButton("📝 Анализ по тексту", callback_data="analyze_text")],
        [InlineKeyboardButton("🎤 Анализ по голосовому", callback_data="analyze_voice")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🍽️ **Анализ блюда**\n\n"
        "Выберите способ анализа:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_addmeal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запроса для addmeal"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if not existing_user:
            await query.edit_message_text(
                "❌ Вы не зарегистрированы в системе!\n"
                "Используйте /register для регистрации."
            )
            return
    except Exception as e:
        logger.error(f"Error in handle_addmeal_callback: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при проверке регистрации. Попробуйте позже."
        )
        return
    
    # Создаем подменю для анализа блюда
    keyboard = [
        [InlineKeyboardButton("📷 Анализ по фото", callback_data="analyze_photo")],
        [InlineKeyboardButton("📝 Анализ по тексту", callback_data="analyze_text")],
        [InlineKeyboardButton("🎤 Анализ по голосовому", callback_data="analyze_voice")],
        [InlineKeyboardButton("📷📝 Фото + Текст", callback_data="analyze_photo_text")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🍽️ **Анализ блюда**\n\n"
        "Выберите способ анализа:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов"""
    query = update.callback_query
    
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
        # Продолжаем обработку даже если не удалось ответить на callback
    
    # Добавляем отладочную информацию
    logger.info(f"Callback query received: {query.data}")
    
    if query.data == "register":
        # Для callback query нужно использовать query.message.reply_text вместо update.message.reply_text
        user = update.effective_user
        
        # Проверяем, зарегистрирован ли пользователь
        try:
            existing_user = check_user_registration(user.id)
            
            if existing_user:
                await query.message.reply_text(
                    "Вы уже зарегистрированы! Используйте /profile для просмотра данных."
                )
                return
        except Exception as e:
            logger.error(f"Error checking user registration: {e}")
            await query.message.reply_text(
                "❌ Произошла ошибка при проверке регистрации. Попробуйте позже."
            )
            return
        
        # Сохраняем состояние регистрации
        context.user_data['registration_step'] = 'name'
        context.user_data['user_data'] = {'telegram_id': user.id}
        
        await query.message.reply_text(
            "Давайте зарегистрируем вас в системе!\n\n"
            "Введите ваше имя:"
        )
    elif query.data == "help":
        await help_command(update, context)
    elif query.data == "main_menu":
        # Просто показываем главное меню в новом сообщении
        await query.message.reply_text(
            "🏠 **Главное меню**\n\n"
            "Выберите нужную функцию:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    elif query.data == "subscription":
        await show_subscription_purchase_menu(update, context)
    elif query.data == "buy_subscription":
        await show_subscription_purchase_menu(update, context)
    elif query.data == "terms":
        await terms_command(update, context)
    elif query.data.startswith('gender_'):
        await handle_gender_callback(update, context)
    elif query.data.startswith('activity_'):
        await handle_activity_callback(update, context)
    elif query.data.startswith('goal_'):
        await handle_goal_callback(update, context)
    elif query.data == "reset_confirm":
        await handle_reset_confirm(update, context)
    elif query.data == "add_dish":
        await handle_add_dish(update, context)
    elif query.data == "check_calories":
        await handle_check_calories(update, context)
    elif query.data == "addmeal":
        await handle_addmeal_callback(update, context)
    elif query.data == "menu_from_meal_selection":
        await handle_menu_from_meal_selection(update, context)
    elif query.data == "profile":
        await handle_profile_callback(update, context)
    elif query.data == "back_to_main":
        await handle_back_to_main(update, context)
    elif query.data.startswith('meal_'):
        await handle_meal_selection(update, context)
    elif query.data == "analyze_photo":
        await handle_analyze_photo_callback(update, context)
    elif query.data == "analyze_text":
        await handle_analyze_text_callback(update, context)
    elif query.data == "analyze_voice":
        await handle_analyze_voice_callback(update, context)
    elif query.data == "analyze_photo_text":
        await handle_analyze_photo_text_callback(update, context)
    elif query.data == "check_photo":
        await handle_check_photo_callback(update, context)
    elif query.data == "check_text":
        await handle_check_text_callback(update, context)
    elif query.data == "check_voice":
        await handle_check_voice_callback(update, context)
    elif query.data == "check_photo_text":
        await handle_check_photo_text_callback(update, context)
    elif query.data == "statistics":
        await handle_statistics_callback(update, context)
    elif query.data == "stats_today":
        await handle_stats_today_callback(update, context)
    elif query.data == "stats_yesterday":
        await handle_stats_yesterday_callback(update, context)
    elif query.data == "stats_week":
        await handle_stats_week_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_stats']:
        await handle_admin_stats_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_users']:
        await handle_admin_users_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_meals']:
        await handle_admin_meals_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_broadcast']:
        await handle_admin_broadcast_callback(update, context)
    elif query.data == "broadcast_create":
        await handle_broadcast_create_callback(update, context)
    elif query.data == "broadcast_stats":
        await handle_broadcast_stats_callback(update, context)
    elif query.data == "broadcast_confirm":
        await handle_broadcast_confirm_callback(update, context)
    elif query.data == "broadcast_cancel":
        await handle_broadcast_cancel_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_subscriptions']:
        await handle_admin_subscriptions_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_check_subscription']:
        await handle_admin_check_subscription_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_manage_subscription']:
        await handle_admin_manage_subscription_callback(update, context)
    elif query.data.startswith(ADMIN_CALLBACKS['admin_activate_trial'] + ':'):
        await handle_admin_activate_trial_callback(update, context)
    elif query.data.startswith(ADMIN_CALLBACKS['admin_activate_premium'] + ':'):
        await handle_admin_activate_premium_callback(update, context)
    elif query.data.startswith(ADMIN_CALLBACKS['admin_deactivate_subscription'] + ':'):
        await handle_admin_deactivate_subscription_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_back']:
        await handle_admin_back_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_panel']:
        await show_admin_panel(update, context)
    elif query.data == "buy_subscription":
        await show_subscription_purchase_menu(update, context)
    elif query.data.startswith("buy_"):
        await handle_subscription_purchase(update, context)
    elif query.data == "separator":
        # Игнорируем нажатие на разделитель
        await query.answer()
    elif query.data == "admin_star_balance":
        await handle_admin_star_balance_callback(update, context)
    elif query.data == "cancel_analysis":
        await handle_cancel_analysis(update, context)
    else:
        # Если callback data не распознан
        logger.warning(f"Unknown callback data: {query.data}")
        await query.message.reply_text(
            "❌ Неизвестная команда. Попробуйте снова.",
            reply_markup=get_main_menu_keyboard()
        )

async def handle_gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора пола"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('gender_'):
        # Проверяем, есть ли данные пользователя
        if 'user_data' not in context.user_data:
            await query.message.reply_text(
                "❌ Ошибка: данные регистрации не найдены.\n"
                "Пожалуйста, начните регистрацию заново с помощью /register"
            )
            return
            
        gender_map = {
            'gender_male': 'Мужской',
            'gender_female': 'Женский'
        }
        
        user_data = context.user_data['user_data']
        user_data['gender'] = gender_map[query.data]
        context.user_data['registration_step'] = 'age'
        
        await query.message.reply_text("Введите ваш возраст:")

async def handle_reset_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подтверждения сброса данных"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Удаляем данные регистрации
        user_deleted = delete_user_by_telegram_id(user.id)
        
        # Удаляем все данные о приемах пищи
        meals_deleted = delete_all_user_meals(user.id)
        
        if user_deleted:
            # Очищаем данные пользователя из контекста
            context.user_data.clear()
            
            # Создаем кнопку для регистрации
            keyboard = [
                [InlineKeyboardButton("📝 Регистрация", callback_data="register")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Формируем сообщение о результатах удаления
            message = "✅ **Данные успешно удалены!**\n\n"
            message += "• Данные регистрации удалены\n"
            if meals_deleted:
                message += "• Все данные о приемах пищи удалены\n"
            else:
                message += "• Данные о приемах пищи не найдены\n"
            message += "\nВсе ваши данные были безвозвратно удалены."
            
            await query.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.message.reply_text(
                "❌ Ошибка: данные не найдены для удаления или произошла ошибка при удалении"
            )
    except Exception as e:
        logger.error(f"Error in handle_reset_confirm: {e}")
        await query.message.reply_text(
            "❌ Произошла ошибка при удалении данных. Попробуйте позже."
        )


async def handle_add_dish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Добавить блюдо'"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем, зарегистрирован ли пользователь
    if not check_user_registration(user.id):
        await query.edit_message_text(
            "❌ **Вы не зарегистрированы!**\n\n"
            "Для использования бота необходимо пройти регистрацию.\n"
            "Нажмите /start для начала регистрации.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Регистрация", callback_data="register")]
            ]),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем подписку
    access_info = check_subscription_access(user.id)
    if not access_info['has_access']:
        subscription_msg = get_subscription_message(access_info)
        await query.edit_message_text(
            subscription_msg,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, какие приемы пищи уже добавлены сегодня
    breakfast_added = is_meal_already_added(user.id, 'meal_breakfast')
    lunch_added = is_meal_already_added(user.id, 'meal_lunch')
    dinner_added = is_meal_already_added(user.id, 'meal_dinner')
    
    # Создаем подменю для выбора приема пищи
    keyboard = []
    
    # Завтрак - только если не добавлен
    if not breakfast_added:
        keyboard.append([InlineKeyboardButton("🌅 Завтрак", callback_data="meal_breakfast")])
    
    # Обед - только если не добавлен
    if not lunch_added:
        keyboard.append([InlineKeyboardButton("☀️ Обед", callback_data="meal_lunch")])
    
    # Ужин - только если не добавлен
    if not dinner_added:
        keyboard.append([InlineKeyboardButton("🌙 Ужин", callback_data="meal_dinner")])
    
    # Перекус - всегда доступен
    keyboard.append([InlineKeyboardButton("🍎 Перекус", callback_data="meal_snack")])
    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Формируем сообщение
    message_text = "🍽️ **Добавить блюдо**\n\n"
    message_text += "Выберите прием пищи:\n\n"
    message_text += "🍎 Перекус можно добавлять неограниченное количество раз"
    
    await query.edit_message_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_menu_from_meal_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Меню' из меню выбора приема пищи - отправляет новое сообщение"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    await query.message.reply_text(
        "🏠 **Главное меню**\n\n"
        "Выберите нужную функцию:",
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )

async def handle_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Профиль' из главного меню"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user.id,))
            user_data = cursor.fetchone()
        
        if not user_data:
            await query.edit_message_text(
                "❌ Вы не зарегистрированы в системе!\n"
                "Используйте /register для регистрации."
            )
            return
    except Exception as e:
        logger.error(f"Error in handle_profile_callback: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении данных профиля. Попробуйте позже."
        )
        return
    
    # Получаем информацию о подписке
    subscription_info = check_user_subscription(user.id)
    logger.info(f"Profile callback - Subscription info for user {user.id}: {subscription_info}")
    
    # Формируем текст о подписке
    subscription_text = ""
    if subscription_info['is_active']:
        if subscription_info['type'] == 'trial':
            subscription_text = f"🆓 **Триальный период**\nДоступен до: {subscription_info['expires_at']}"
        elif subscription_info['type'] == 'premium':
            if subscription_info['expires_at']:
                subscription_text = f"⭐ **Премиум подписка**\nДействует до: {subscription_info['expires_at']}"
            else:
                subscription_text = "⭐ **Премиум подписка**\nБез ограничений"
    else:
        if subscription_info['type'] == 'trial_expired':
            subscription_text = f"❌ **Триальный период истек**\nИстек: {subscription_info['expires_at']}"
        elif subscription_info['type'] == 'premium_expired':
            subscription_text = f"❌ **Премиум подписка истекла**\nИстекла: {subscription_info['expires_at']}"
        else:
            subscription_text = "❌ **Нет активной подписки**"
    
    # Получаем информацию о цели и целевой норме калорий
    goal = user_data[13] if len(user_data) > 13 else 'maintain'
    target_calories = int(user_data[14]) if len(user_data) > 14 and user_data[14] else int(user_data[8])
    
    # Формируем текст о цели
    goal_text = GOALS.get(goal, 'Держать себя в форме')
    goal_emoji = "📉" if goal == 'lose_weight' else "⚖️" if goal == 'maintain' else "📈"
    
    profile_text = f"""
👤 **Ваш профиль:**

📝 **Имя:** {user_data[2]}
👤 **Пол:** {user_data[3]}
🎂 **Возраст:** {user_data[4]} лет
📏 **Рост:** {user_data[5]} см
⚖️ **Вес:** {user_data[6]} кг
🏃 **Уровень активности:** {user_data[7]}
🎯 **Цель:** {goal_emoji} {goal_text}
📊 **Расчетная норма:** {user_data[8]} ккал
🎯 **Целевая норма:** {target_calories} ккал
📅 **Дата регистрации:** {user_data[9]}

{subscription_text}
    """
    
    # Создаем клавиатуру
    keyboard = []
    
    # Если подписка неактивна, добавляем кнопку покупки
    if not subscription_info['is_active']:
        keyboard.append([InlineKeyboardButton("💎 Купить подписку", callback_data="buy_subscription")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        profile_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_check_photo_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Фото + Текст' для проверки калорий"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем подписку и лимит использований
    access_info = check_subscription_access(user.id)
    if not access_info['has_access']:
        daily_checks = get_daily_calorie_checks_count(user.id)
        if daily_checks >= 3:
            limit_msg = f"❌ **Лимит использований исчерпан**\n\n"
            limit_msg += f"Вы использовали функцию 'Узнать калории' {daily_checks}/3 раз сегодня.\n\n"
            limit_msg += f"⏰ **Счетчик сбрасывается в полночь**\n\n"
            limit_msg += f"💡 **Для неограниченного использования оформите подписку:**\n"
            limit_msg += f"• 1 день - 50 ⭐\n"
            limit_msg += f"• 7 дней - 200 ⭐\n"
            limit_msg += f"• 30 дней - 500 ⭐\n"
            limit_msg += f"• 90 дней - 1200 ⭐\n"
            limit_msg += f"• 365 дней - 4000 ⭐\n\n"
            limit_msg += f"💎 Безопасно • Мгновенно • Без комиссий"
            
            await query.edit_message_text(
                limit_msg,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            return
    
    # Устанавливаем состояние ожидания фото
    context.user_data['waiting_for_check_photo_text'] = True
    
    await query.edit_message_text(
        "📷📝 **Комбинированный анализ блюда**\n\n"
        "**Шаг 1:** Отправьте фото блюда\n\n"
        "**Шаг 2:** После анализа фото отправьте текстовое описание с уточнениями:\n"
        "• Размер порции (\"большая тарелка\", \"2 куска\", \"примерно 300г\")\n"
        "• Дополнительные ингредиенты (\"с добавлением сыра\", \"без масла\")\n"
        "• Способ приготовления (\"домашний рецепт\", \"жареное\")\n\n"
        "**Примеры уточнений:**\n"
        "• \"Большая порция, диаметр 30см, с добавлением моцареллы\"\n"
        "• \"2 куска, домашний рецепт, без масла\"\n"
        "• \"Примерно 250г, с двойной порцией мяса\"\n\n"
        "⚠️ **Для более точного расчета на фото должны присутствовать якорные объекты:**\n"
        "• Вилка, ложка, рука, монета или другие объекты для масштаба\n\n"
        "ℹ️ **Результат будет показан, но НЕ сохранится в вашу статистику**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]),
        parse_mode='Markdown'
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий"""
    is_for_adding = context.user_data.get('waiting_for_photo', False)
    is_for_checking = context.user_data.get('waiting_for_check_photo', False)
    is_for_photo_text = context.user_data.get('waiting_for_photo_text', False)
    is_for_check_photo_text = context.user_data.get('waiting_for_check_photo_text', False)
    
    if not (is_for_adding or is_for_checking or is_for_photo_text or is_for_check_photo_text):
        return
    
    user = update.effective_user
    photo = update.message.photo[-1]  # Берем фото в наилучшем качестве
    
    # Сбрасываем состояние ожидания
    context.user_data['waiting_for_photo'] = False
    context.user_data['waiting_for_check_photo'] = False
    context.user_data['waiting_for_photo_text'] = False
    context.user_data['waiting_for_check_photo_text'] = False
    
    # Отправляем сообщение о начале обработки
    processing_msg = await update.message.reply_text(
        "🔄 **Обрабатываю фотографию...**\n\n"
        "Анализирую изображение с помощью ИИ модели...",
        parse_mode='Markdown'
    )
    
    try:
        # Получаем файл фотографии
        file = await context.bot.get_file(photo.file_id)
        file_url = file.file_path
        
        logger.info(f"Downloading photo from: {file_url}")
        
        # Скачиваем изображение асинхронно с исправленными SSL настройками
        import aiohttp
        import ssl
        
        # Создаем SSL контекст с мягкими настройками
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            if file_url.startswith('https://'):
                url = file_url
            else:
                url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_url}"
            
            async with session.get(url) as response:
                logger.info(f"Photo download response: {response.status}")
                
                if response.status != 200:
                    logger.error(f"Failed to download photo: {response.status}")
                    await processing_msg.edit_text(
                        f"❌ Ошибка при загрузке фотографии\n\n"
                        f"Код ошибки: {response.status}\n"
                        f"URL: {url}\n"
                        f"Попробуйте отправить фото еще раз или используйте команду /addphoto"
                    )
                    return
                
                # Читаем содержимое файла
                image_content = await response.read()
        
        # Отправляем запрос к языковой модели
        logger.info("Starting food photo analysis...")
        analysis_result = await analyze_food_photo(image_content)
        logger.info(f"Analysis result: {analysis_result is not None}")
        
        if analysis_result:
            logger.info(f"Analysis result length: {len(analysis_result)}")
            logger.info(f"Analysis result preview: {analysis_result[:200]}...")
        
        # Получаем информацию о выбранном приеме пищи
        selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
        
        # Проверяем валидность анализа
        is_valid = is_valid_analysis(analysis_result) if analysis_result else False
        logger.info(f"Analysis is valid: {is_valid}")
        
        if analysis_result and is_valid:
            # Удаляем пояснения из анализа
            analysis_result = remove_explanations_from_analysis(analysis_result)
            
            # Парсим результат анализа для извлечения калорий
            calories = extract_calories_from_analysis(analysis_result)
            dish_name = extract_dish_name_from_analysis(analysis_result) or "Блюдо по фото"
            
            # Проверяем комбинированный режим
            if is_for_photo_text or is_for_check_photo_text:
                # Сохраняем результат анализа фото для последующего объединения с текстом
                context.user_data['photo_analysis_result'] = analysis_result
                context.user_data['photo_dish_name'] = dish_name
                context.user_data['photo_calories'] = calories
                
                # Устанавливаем состояние ожидания текста
                if is_for_photo_text:
                    context.user_data['waiting_for_text_after_photo'] = True
                else:
                    context.user_data['waiting_for_check_text_after_photo'] = True
                
                await processing_msg.edit_text(
                    "📷 **Фото проанализировано!**\n\n"
                    "Теперь отправьте текстовое описание с уточнениями:\n"
                    "• Размер порции\n"
                    "• Дополнительные ингредиенты\n"
                    "• Способ приготовления\n\n"
                    "**Пример:** \"Большая порция, диаметр 30см, с добавлением моцареллы\"",
                    parse_mode='Markdown'
                )
                return
            
            # Проверяем режим - добавление или проверка калорий
            is_check_mode = context.user_data.get('check_mode', False)
            
            if is_check_mode:
                # Режим проверки калорий - только показываем результат
                # Записываем использование функции
                add_calorie_check(user.id, 'photo')
                
                cleaned_result = clean_markdown_text(analysis_result)
                result_text = f"🔍 **Анализ калорий**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ сохранены в статистику**"
                
                await processing_msg.edit_text(
                    result_text, 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
                    ]), 
                    parse_mode='Markdown'
                )
                # Сбрасываем режим проверки
                context.user_data['check_mode'] = False
            else:
                # Режим добавления блюда - сохраняем в базу
                meal_info = f"**🍽️ {selected_meal}**\n\n{analysis_result}"
                
                # Сохраняем данные о приеме пищи в базу данных
                try:
                    meal_type = context.user_data.get('selected_meal', 'meal_breakfast')
                    
                    logger.info(f"Attempting to save meal for user {user.id}: meal_type={meal_type}, meal_name={selected_meal}, dish_name={dish_name}, calories={calories}")
                    
                    # Сохраняем в базу данных
                    success = add_meal(
                        telegram_id=user.id,
                        meal_type=meal_type,
                        meal_name=selected_meal,
                        dish_name=dish_name,
                        calories=calories,
                        analysis_type="photo"
                    )
                    
                    logger.info(f"Meal save result: {success}")
                    
                    if success:
                        logger.info(f"Meal saved successfully for user {user.id}")
                        cleaned_meal_info = clean_markdown_text(meal_info)
                        await processing_msg.edit_text(cleaned_meal_info, reply_markup=get_analysis_result_keyboard(), parse_mode='Markdown')
                    else:
                        logger.warning(f"Failed to save meal for user {user.id}")
                        await processing_msg.edit_text(
                            "❌ Ошибка сохранения\n\n"
                            "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                            reply_markup=get_main_menu_keyboard()
                        )
                    
                except Exception as e:
                    logger.error(f"Error saving meal to database: {e}")
                    await processing_msg.edit_text(
                        "❌ Ошибка сохранения\n\n"
                        "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                        reply_markup=get_main_menu_keyboard()
                )
        elif analysis_result:
            # ИИ вернул результат, но не смог определить калории
            logger.warning(f"Analysis returned but is not valid. Result: {analysis_result[:200]}...")
            await processing_msg.edit_text(
                "❌ **Анализ не удался**\n\n"
                "ИИ не смог определить калорийность блюда на фотографии.\n\n"
                "**Возможные причины:**\n"
                "• На фото нет еды или еда не видна\n"
                "• Слишком темное или размытое изображение\n"
                "• Отсутствуют якорные объекты для масштаба\n\n"
                "**Рекомендации:**\n"
                "• Убедитесь, что на фото четко видна еда\n"
                "• Добавьте вилку, ложку или руку для масштаба\n"
                "• Сделайте фото при хорошем освещении\n\n"
                "Попробуйте отправить другое фото или используйте команду /addtext для текстового описания.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            # ИИ не вернул результат
            logger.error("No analysis result returned from API")
            await processing_msg.edit_text(
                "❌ **Ошибка анализа**\n\n"
                "Не удалось проанализировать фотографию. Возможные причины:\n"
                "• Проблемы с подключением к серверу\n"
                "• Неподдерживаемый формат изображения\n"
                "• Слишком большой размер файла\n\n"
                "Попробуйте отправить другое фото или используйте команду /addtext для текстового описания.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка\n\n"
            "Не удалось обработать фотографию. Попробуйте позже или используйте команду /addphoto снова.",
            reply_markup=get_main_menu_keyboard()
        )


async def handle_food_text_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик анализа текстового описания блюда"""
    user = update.effective_user
    description = update.message.text
    
    # Сбрасываем состояние ожидания
    context.user_data['waiting_for_text'] = False
    context.user_data['waiting_for_check_text'] = False
    context.user_data['waiting_for_text_after_photo'] = False
    context.user_data['waiting_for_check_text_after_photo'] = False
    
    # Отправляем сообщение о начале обработки
    processing_msg = await update.message.reply_text(
        "🔄 **Анализирую описание блюда...**\n\n"
        "Обрабатываю текст с помощью ИИ модели...",
        parse_mode='Markdown'
    )
    
    try:
        # Отправляем запрос к языковой модели
        analysis_result = await analyze_food_text(description)
        
        if analysis_result and is_valid_analysis(analysis_result):
            # Удаляем пояснения из анализа
            analysis_result = remove_explanations_from_analysis(analysis_result)
            
            # Логируем результат анализа для отладки
            logger.info(f"Analysis result for '{description}': {analysis_result}")
            
            # Парсим результат анализа для извлечения калорий
            calories = extract_calories_from_analysis(analysis_result)
            
            # Если не удалось извлечь калории, пробуем использовать вес из описания
            if not calories:
                # Извлекаем вес из описания
                weight_grams = extract_weight_from_description(description)
                if weight_grams:
                    logger.info(f"Extracted weight from description: {weight_grams}г")
                    # Ищем калорийность на 100г в анализе
                    calories_per_100g = extract_calories_per_100g_from_analysis(analysis_result)
                    if calories_per_100g:
                        calories = int((calories_per_100g * weight_grams) / 100)
                        logger.info(f"Calculated total calories: {calories} from {calories_per_100g} ккал/100г × {weight_grams}г")
            
            dish_name = extract_dish_name_from_analysis(analysis_result) or description[:50]
            
            # Проверяем комбинированный режим
            if context.user_data.get('waiting_for_text_after_photo') or context.user_data.get('waiting_for_check_text_after_photo'):
                # Объединяем результаты анализа фото и текста
                photo_analysis = context.user_data.get('photo_analysis_result', '')
                photo_dish_name = context.user_data.get('photo_dish_name', 'Блюдо')
                photo_calories = context.user_data.get('photo_calories', 0)
                
                # Создаем комбинированный анализ
                combined_analysis = f"📷 **Анализ фото:**\n{photo_analysis}\n\n"
                combined_analysis += f"📝 **Текстовые уточнения:**\n{description}\n\n"
                combined_analysis += f"🔍 **Комбинированный анализ:**\n{analysis_result}"
                
                # Очищаем временные данные
                context.user_data.pop('photo_analysis_result', None)
                context.user_data.pop('photo_dish_name', None)
                context.user_data.pop('photo_calories', None)
                
                # Определяем режим
                is_check_mode = context.user_data.get('waiting_for_check_text_after_photo', False)
                
                if is_check_mode:
                    # Режим проверки калорий
                    add_calorie_check(user.id, 'photo_text')
                    
                    cleaned_result = clean_markdown_text(combined_analysis)
                    result_text = f"🔍 **Комбинированный анализ калорий**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ сохранены в статистику**"
                    
                    await processing_msg.edit_text(
                        result_text, 
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
                        ]), 
                        parse_mode='Markdown'
                    )
                else:
                    # Режим добавления блюда
                    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
                    meal_info = f"**🍽️ {selected_meal}**\n\n{combined_analysis}"
                    
                    # Сохраняем в базу данных
                    try:
                        meal_type = context.user_data.get('selected_meal', 'meal_breakfast')
                        
                        success = add_meal(
                            telegram_id=user.id,
                            meal_type=meal_type,
                            dish_name=dish_name,
                            calories=calories,
                            meal_info=meal_info
                        )
                        
                        if success:
                            await processing_msg.edit_text(
                                f"✅ **Блюдо добавлено в {selected_meal}!**\n\n"
                                f"🍽️ **Блюдо:** {dish_name}\n"
                                f"🔥 **Калории:** {calories} ккал\n\n"
                                f"📊 **Детальный анализ:**\n{clean_markdown_text(combined_analysis)}",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("🔙 Назад к приемам пищи", callback_data="add_dish")]
                                ]),
                                parse_mode='Markdown'
                            )
                        else:
                            await processing_msg.edit_text(
                                "❌ Ошибка при сохранении блюда. Попробуйте еще раз.",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("🔙 Назад к приемам пищи", callback_data="add_dish")]
                                ])
                            )
                    except Exception as e:
                        logger.error(f"Error saving meal: {e}")
                        await processing_msg.edit_text(
                            "❌ Ошибка при сохранении блюда. Попробуйте еще раз.",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("🔙 Назад к приемам пищи", callback_data="add_dish")]
                            ])
                        )
                return
            
            # Проверяем режим - добавление или проверка калорий
            is_check_mode = context.user_data.get('check_mode', False)
            is_auto_save = context.user_data.get('auto_save', False)
            
            if is_check_mode and not is_auto_save:
                # Режим проверки калорий - только показываем результат
                # Записываем использование функции
                add_calorie_check(user.id, 'text')
                
                cleaned_result = clean_markdown_text(analysis_result)
                result_text = f"🔍 **Анализ калорий**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ сохранены в статистику**"
                
                await processing_msg.edit_text(
                    result_text, 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
                    ]), 
                    parse_mode='Markdown'
                )
                # Сбрасываем режим проверки
                context.user_data['check_mode'] = False
            else:
                # Режим добавления блюда - сохраняем в базу
                try:
                    meal_type = context.user_data.get('selected_meal', 'meal_breakfast')
                    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
                    
                    # Сохраняем в базу данных
                    success = add_meal(
                        telegram_id=user.id,
                        meal_type=meal_type,
                        meal_name=selected_meal,
                        dish_name=dish_name,
                        calories=calories,
                        analysis_type="text"
                    )
                    
                    if success:
                        logger.info(f"Meal saved successfully for user {user.id}")
                        cleaned_result = clean_markdown_text(analysis_result)
                        await processing_msg.edit_text(cleaned_result, reply_markup=get_analysis_result_keyboard(), parse_mode='Markdown')
                    else:
                        logger.warning(f"Failed to save meal for user {user.id}")
                        await processing_msg.edit_text(
                            "❌ Ошибка сохранения\n\n"
                            "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                            reply_markup=get_main_menu_keyboard()
                        )
                    
                except Exception as e:
                    logger.error(f"Error saving meal to database: {e}")
                    await processing_msg.edit_text(
                        "❌ Ошибка сохранения\n\n"
                        "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                        reply_markup=get_main_menu_keyboard()
                )
        elif analysis_result:
            # ИИ вернул результат, но не смог определить калории
            await processing_msg.edit_text(
                "❌ **Анализ не удался**\n\n"
                "ИИ не смог определить калорийность блюда по описанию.\n\n"
                "**Возможные причины:**\n"
                "• Описание слишком краткое или неясное\n"
                "• Не указан размер порции\n"
                "• Отсутствуют основные ингредиенты\n\n"
                "**Рекомендации:**\n"
                "• Укажите точные ингредиенты и их количество\n"
                "• Добавьте размер порции (например, 'большая тарелка', '2 куска')\n"
                "• Опишите способ приготовления\n\n"
                "Попробуйте дать более подробное описание или используйте команду /addphoto для анализа фото.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            # API не работает или анализ не удался
            await processing_msg.edit_text(
                "❌ **Ошибка анализа**\n\n"
                "Не удалось проанализировать описание блюда. Попробуйте:\n"
                "• Указать более подробное описание\n"
                "• Включить размер порции (например, '300г', 'большая тарелка')\n"
                "• Перечислить основные ингредиенты\n"
                "• Указать способ приготовления\n\n"
                "**Примеры правильных описаний:**\n"
                "• \"Борщ с мясом, 300г\"\n"
                "• \"Салат Цезарь с курицей, большая порция\"\n"
                "• \"Пицца Маргарита, 2 куска\"\n\n"
                "Попробуйте команду /addtext снова.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing text description: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка\n\n"
            "Не удалось обработать описание блюда. Попробуйте позже или используйте команду /addtext снова.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        # Очищаем флаги режимов
        context.user_data.pop('auto_save', None)
        context.user_data.pop('save_mode', None)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик голосовых сообщений"""
    is_for_adding = context.user_data.get('waiting_for_voice', False)
    is_for_checking = context.user_data.get('waiting_for_check_voice', False)
    
    if not (is_for_adding or is_for_checking):
        return
    
    user = update.effective_user
    voice = update.message.voice
    
    # Сбрасываем состояние ожидания
    context.user_data['waiting_for_voice'] = False
    context.user_data['waiting_for_check_voice'] = False
    
    # Отправляем сообщение о начале обработки
    processing_msg = await update.message.reply_text(
        "🔄 **Обрабатываю голосовое сообщение...**\n\n"
        "Преобразую речь в текст и анализирую с помощью ИИ...",
        parse_mode='Markdown'
    )
    
    try:
        # Получаем файл голосового сообщения
        file = await context.bot.get_file(voice.file_id)
        file_url = file.file_path
        
        logger.info(f"Downloading voice from: {file_url}")
        
        # Скачиваем аудиофайл асинхронно с исправленными SSL настройками
        import aiohttp
        import ssl
        
        # Создаем SSL контекст с мягкими настройками
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            if file_url.startswith('https://'):
                url = file_url
            else:
                url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_url}"
            
            async with session.get(url) as response:
                logger.info(f"Voice download response: {response.status}")
                
                if response.status != 200:
                    logger.error(f"Failed to download voice: {response.status}")
                    await processing_msg.edit_text(
                        f"❌ Ошибка при загрузке голосового сообщения\n\n"
                        f"Код ошибки: {response.status}\n"
                        f"URL: {url}\n"
                        f"Попробуйте отправить голосовое сообщение еще раз или используйте команду /addvoice"
                    )
                    return
                
                # Читаем содержимое файла
                audio_content = await response.read()
        
        # Конвертируем в base64
        audio_data = base64.b64encode(audio_content).decode('utf-8')
        
        # Отправляем запрос к языковой модели для распознавания речи
        transcription_result = await transcribe_voice(audio_data)
        
        if not transcription_result:
            await processing_msg.edit_text(
                "❌ Ошибка распознавания речи\n\n"
                "Не удалось распознать голосовое сообщение. Попробуйте:\n"
                "• Говорить четче и медленнее\n"
                "• Убедиться, что микрофон работает\n"
                "• Использовать команду /addtext для текстового описания\n\n"
                "Попробуйте команду /addvoice снова."
            )
            return
        
        # Анализируем распознанный текст
        analysis_result = await analyze_food_text(transcription_result)
        
        if analysis_result and is_valid_analysis(analysis_result):
            # Удаляем пояснения из анализа
            analysis_result = remove_explanations_from_analysis(analysis_result)
            
            # Парсим результат анализа для извлечения калорий
            calories = extract_calories_from_analysis(analysis_result)
            dish_name = extract_dish_name_from_analysis(analysis_result) or transcription_result[:50]
            
            # Проверяем режим - добавление или проверка калорий
            is_check_mode = context.user_data.get('check_mode', False)
            
            if is_check_mode:
                # Режим проверки калорий - только показываем результат
                # Записываем использование функции
                add_calorie_check(user.id, 'voice')
                
                cleaned_result = clean_markdown_text(analysis_result)
                result_text = f"🔍 **Анализ калорий**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ сохранены в статистику**"
                
                await processing_msg.edit_text(
                    result_text, 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
                    ]), 
                    parse_mode='Markdown'
                )
                # Сбрасываем режим проверки
                context.user_data['check_mode'] = False
            else:
                # Режим добавления блюда - сохраняем в базу
                try:
                    meal_type = context.user_data.get('selected_meal', 'meal_breakfast')
                    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
                    
                    # Сохраняем в базу данных
                    success = add_meal(
                        telegram_id=user.id,
                        meal_type=meal_type,
                        meal_name=selected_meal,
                        dish_name=dish_name,
                        calories=calories,
                        analysis_type="voice"
                    )
                    
                    if success:
                        logger.info(f"Meal saved successfully for user {user.id}")
                        # Добавляем информацию о распознанном тексте
                        cleaned_result = clean_markdown_text(analysis_result)
                        result_with_transcription = f"**🎤 Распознанный текст:** {transcription_result}\n\n{cleaned_result}"
                        await processing_msg.edit_text(result_with_transcription, reply_markup=get_analysis_result_keyboard(), parse_mode='Markdown')
                    else:
                        logger.warning(f"Failed to save meal for user {user.id}")
                        await processing_msg.edit_text(
                            "❌ Ошибка сохранения\n\n"
                            "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                            reply_markup=get_main_menu_keyboard()
                        )
                    
                except Exception as e:
                    logger.error(f"Error saving meal to database: {e}")
                    await processing_msg.edit_text(
                        "❌ Ошибка сохранения\n\n"
                        "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                        reply_markup=get_main_menu_keyboard()
                )
        elif analysis_result:
            # ИИ вернул результат, но не смог определить калории
            await processing_msg.edit_text(
                f"**🎤 Распознанный текст:** {transcription_result}\n\n"
                "❌ **Анализ не удался**\n\n"
                "ИИ не смог определить калорийность блюда по описанию.\n\n"
                "**Возможные причины:**\n"
                "• Описание слишком краткое или неясное\n"
                "• Не указан размер порции\n"
                "• Отсутствуют основные ингредиенты\n\n"
                "**Рекомендации:**\n"
                "• Укажите точные ингредиенты и их количество\n"
                "• Добавьте размер порции (например, 'большая тарелка', '2 куска')\n"
                "• Опишите способ приготовления\n\n"
                "Попробуйте дать более подробное описание или используйте команду /addphoto для анализа фото.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await processing_msg.edit_text(
                f"**🎤 Распознанный текст:** {transcription_result}\n\n"
                "❌ **Ошибка анализа**\n\n"
                "Не удалось проанализировать описание блюда. Попробуйте:\n"
                "• Указать более подробное описание\n"
                "• Включить размер порции\n"
                "• Перечислить основные ингредиенты\n\n"
                "Попробуйте команду /addvoice снова.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка\n\n"
            "Не удалось обработать голосовое сообщение. Попробуйте позже или используйте команду /addvoice снова.",
            reply_markup=get_main_menu_keyboard()
        )

# ==================== АДМИН ФУНКЦИИ ====================

async def handle_admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Статистика' в админке"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if not is_admin(user.id):
        await query.message.reply_text("❌ У вас нет прав доступа!")
        return
    
    try:
        # Получаем детальную статистику
        user_count = get_user_count()
        meals_count = get_meals_count()
        daily_stats = get_daily_stats()
        
        # Получаем статистику за последние 7 дней
        week_stats = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            # Здесь можно добавить функцию для получения статистики по дням
            week_stats[date] = 0  # Заглушка
        
        stats_text = f"""
📊 **Детальная статистика**

👥 **Пользователи:**
• Всего зарегистрировано: {user_count}
• Активных сегодня: {daily_stats['active_users']}

🍽️ **Приемы пищи:**
• Всего записей: {meals_count}
• За сегодня: {daily_stats['meals_today']}
• Общих калорий сегодня: {daily_stats['total_calories']}

📈 **Активность за неделю:**
• Понедельник: 0 записей
• Вторник: 0 записей  
• Среда: 0 записей
• Четверг: 0 записей
• Пятница: 0 записей
• Суббота: 0 записей
• Воскресенье: {daily_stats['meals_today']} записей
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing admin stats: {e}")
        await query.message.reply_text(
            "❌ Ошибка при получении статистики. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
            ])
        )

async def handle_admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Пользователи' в админке"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if not is_admin(user.id):
        await query.message.reply_text("❌ У вас нет прав доступа!")
        return
    
    try:
        # Получаем список пользователей
        users = get_all_users_for_admin()
        
        if not users:
            await query.message.reply_text(
                "👥 **Пользователи**\n\n"
                "Пользователи не найдены.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
                ])
            )
            return
        
        # Формируем список пользователей (показываем только первые 10)
        users_text = "👥 **Пользователи**\n\n"
        for i, user_data in enumerate(users[:10], 1):
            users_text += f"{i}. **{user_data[1]}** (ID: {user_data[0]})\n"
            users_text += f"   Пол: {user_data[2]}, Возраст: {user_data[3]}\n"
            users_text += f"   Рост: {user_data[4]}см, Вес: {user_data[5]}кг\n"
            users_text += f"   Норма калорий: {user_data[7]} ккал\n"
            users_text += f"   Регистрация: {user_data[8][:10]}\n\n"
        
        if len(users) > 10:
            users_text += f"... и еще {len(users) - 10} пользователей"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(users_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing admin users: {e}")
        await query.message.reply_text(
            "❌ Ошибка при получении списка пользователей. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
            ])
        )

async def handle_admin_meals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Последние приемы пищи' в админке"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if not is_admin(user.id):
        await query.message.reply_text("❌ У вас нет прав доступа!")
        return
    
    try:
        # Получаем последние записи о приемах пищи
        meals = get_recent_meals(10)
        
        if not meals:
            await query.message.reply_text(
                "🍽️ **Последние приемы пищи**\n\n"
                "Записи о приемах пищи не найдены.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
                ])
            )
            return
        
        meals_text = "🍽️ **Последние приемы пищи**\n\n"
        for i, meal in enumerate(meals, 1):
            user_name = meal[1] or f"ID: {meal[0]}"
            meals_text += f"{i}. **{user_name}**\n"
            meals_text += f"   {meal[2]}: {meal[3]} ({meal[4]} ккал)\n"
            meals_text += f"   Тип: {meal[5]}, Время: {meal[6][:16]}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(meals_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing admin meals: {e}")
        await query.message.reply_text(
            "❌ Ошибка при получении записей о приемах пищи. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
            ])
        )

async def handle_admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Рассылка' в админке"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if not is_admin(user.id):
        await query.message.reply_text("❌ У вас нет прав доступа!")
        return
    
    # Получаем количество пользователей
    users = get_all_users_for_broadcast()
    user_count = len(users)
    
    await query.edit_message_text(
        f"📢 **Рассылка**\n\n"
        f"👥 **Всего пользователей:** {user_count}\n\n"
        f"Выберите действие:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Создать рассылку", callback_data="broadcast_create")],
            [InlineKeyboardButton("📊 Статистика рассылок", callback_data="broadcast_stats")],
            [InlineKeyboardButton("🔙 Назад в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
        ]),
        parse_mode='Markdown'
    )

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

async def handle_broadcast_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик создания рассылки"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if not is_admin(user.id):
        await query.message.reply_text("❌ У вас нет прав доступа!")
        return
    
    # Устанавливаем состояние ожидания текста рассылки
    context.user_data['waiting_for_broadcast_text'] = True
    
    await query.edit_message_text(
        "📝 **Создание рассылки**\n\n"
        "Отправьте текст сообщения для рассылки.\n\n"
        "**Поддерживается Markdown форматирование:**\n"
        "• **жирный текст**\n"
        "• *курсив*\n"
        "• `моноширинный`\n"
        "• [ссылка](https://example.com)\n\n"
        "**Пример:**\n"
        "Привет! 👋\n\n"
        "У нас **новые функции** в боте:\n"
        "• Улучшенный анализ калорий\n"
        "• Новые рецепты\n\n"
        "Попробуйте прямо сейчас! 🚀",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="broadcast_cancel")]
        ]),
        parse_mode='Markdown'
    )

async def handle_broadcast_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик статистики рассылок"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if not is_admin(user.id):
        await query.message.reply_text("❌ У вас нет прав доступа!")
        return
    
    # Получаем статистику пользователей
    users = get_all_users_for_broadcast()
    user_count = len(users)
    
    await query.edit_message_text(
        f"📊 **Статистика рассылок**\n\n"
        f"👥 **Всего пользователей:** {user_count}\n"
        f"📅 **Последняя рассылка:** Не проводилась\n"
        f"📈 **Средний процент доставки:** -%\n\n"
        f"*Статистика будет обновляться после проведения рассылок*",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад к рассылке", callback_data=ADMIN_CALLBACKS['admin_broadcast'])],
            [InlineKeyboardButton("🏠 Главная админка", callback_data=ADMIN_CALLBACKS['admin_panel'])]
        ]),
        parse_mode='Markdown'
    )

async def handle_broadcast_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подтверждения рассылки"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if not is_admin(user.id):
        await query.message.reply_text("❌ У вас нет прав доступа!")
        return
    
    # Получаем текст рассылки
    broadcast_text = context.user_data.get('broadcast_text', '')
    if not broadcast_text:
        await query.edit_message_text(
            "❌ Текст рассылки не найден. Попробуйте создать рассылку заново.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к рассылке", callback_data=ADMIN_CALLBACKS['admin_broadcast'])]
            ])
        )
        return
    
    # Очищаем состояние
    context.user_data.pop('waiting_for_broadcast_text', None)
    context.user_data.pop('broadcast_text', None)
    
    # Запускаем рассылку
    bot = context.bot
    stats = await send_broadcast_message(bot, broadcast_text, user.id)
    
    # Показываем результат
    await query.edit_message_text(
        f"✅ **Рассылка завершена!**\n\n"
        f"📊 **Статистика:**\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"✅ Успешно отправлено: {stats['sent_count']}\n"
        f"❌ Ошибок: {stats['failed_count']}\n"
        f"🚫 Заблокировали бота: {stats['blocked_count']}\n"
        f"📈 Процент доставки: {(stats['sent_count']/stats['total_users']*100):.1f}%",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Обратно в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
        ]),
        parse_mode='Markdown'
    )

async def handle_broadcast_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отмены рассылки"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем состояние
    context.user_data.pop('waiting_for_broadcast_text', None)
    context.user_data.pop('broadcast_text', None)
    
    # Возвращаемся к меню рассылки
    await handle_admin_broadcast_callback(update, context)

async def handle_broadcast_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода текста рассылки"""
    user = update.effective_user
    message_text = update.message.text
    
    # Проверяем права админа
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав доступа!")
        return
    
    # Сохраняем текст рассылки
    context.user_data['broadcast_text'] = message_text
    
    # Получаем количество пользователей
    users = get_all_users_for_broadcast()
    user_count = len(users)
    
    # Показываем предварительный просмотр
    await update.message.reply_text(
        f"📝 **Предварительный просмотр рассылки**\n\n"
        f"👥 **Получателей:** {user_count} пользователей\n\n"
        f"📄 **Текст сообщения:**\n"
        f"📢 **Рассылка от Calorigram**\n\n{message_text}\n\n"
        f"**Подтвердить отправку?**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Отправить рассылку", callback_data="broadcast_confirm")],
            [InlineKeyboardButton("❌ Отмена", callback_data="broadcast_cancel")]
        ]),
        parse_mode='Markdown'
    )

async def handle_admin_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Главное меню' в админке"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🏠 **Главное меню**\n\n"
        "Выберите нужную функцию:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

# ==================== ФУНКЦИИ УПРАВЛЕНИЯ ПОДПИСКАМИ ====================

async def handle_admin_subscriptions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Управление подписками' в админке"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    subscriptions_text = """
⭐ **Управление подписками**

Выберите действие:
    """
    
    keyboard = [
        [InlineKeyboardButton("🔍 Проверить подписку", callback_data=ADMIN_CALLBACKS['admin_check_subscription'])],
        [InlineKeyboardButton("🔙 Назад в админку", callback_data=ADMIN_CALLBACKS['admin_panel'])]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        subscriptions_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_admin_check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Проверить подписку' в админке"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    # Сохраняем состояние ожидания ввода Telegram ID
    context.user_data['admin_waiting_for_telegram_id'] = True
    logger.info(f"Set admin_waiting_for_telegram_id=True for user {user.id}")
    
    await query.message.reply_text(
        "🔍 **Проверка подписки**\n\n"
        "Введите Telegram ID пользователя для проверки подписки:",
        parse_mode='Markdown'
    )

async def handle_admin_manage_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик управления подпиской конкретного пользователя"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    # Получаем Telegram ID из callback data
    if ':' in query.data:
        telegram_id = int(query.data.split(':')[1])
    else:
        await query.message.reply_text("❌ Ошибка: не удалось получить ID пользователя")
        return
    
    # Получаем информацию о пользователе
    user_data = get_user_by_telegram_id(telegram_id)
    if not user_data:
        await query.message.reply_text("❌ Пользователь не найден в базе данных!")
        return
    
    # Получаем информацию о подписке
    subscription_info = check_user_subscription(telegram_id)
    
    # Формируем текст о подписке
    subscription_text = ""
    if subscription_info['is_active']:
        if subscription_info['type'] == 'trial':
            subscription_text = f"🆓 **Триальный период**\nДоступен до: {subscription_info['expires_at']}"
        elif subscription_info['type'] == 'premium':
            if subscription_info['expires_at']:
                subscription_text = f"⭐ **Премиум подписка**\nДействует до: {subscription_info['expires_at']}"
            else:
                subscription_text = "⭐ **Премиум подписка**\nБез ограничений"
    else:
        if subscription_info['type'] == 'trial_expired':
            subscription_text = f"❌ **Триальный период истек**\nИстек: {subscription_info['expires_at']}"
        elif subscription_info['type'] == 'premium_expired':
            subscription_text = f"❌ **Премиум подписка истекла**\nИстекла: {subscription_info['expires_at']}"
        else:
            subscription_text = "❌ **Нет активной подписки**"
    
    manage_text = f"""
👤 **Управление подпиской пользователя**

📝 **Имя:** {user_data[2]}
🆔 **Telegram ID:** {telegram_id}
📅 **Дата регистрации:** {user_data[9]}

{subscription_text}

Выберите действие:
    """
    
    keyboard = [
        [InlineKeyboardButton("🆓 Активировать триал (1 день)", callback_data=f"{ADMIN_CALLBACKS['admin_activate_trial']}:{telegram_id}")],
        [InlineKeyboardButton("⭐ Активировать премиум (30 дней)", callback_data=f"{ADMIN_CALLBACKS['admin_activate_premium']}:{telegram_id}")],
        [InlineKeyboardButton("❌ Деактивировать подписку", callback_data=f"{ADMIN_CALLBACKS['admin_deactivate_subscription']}:{telegram_id}")],
        [InlineKeyboardButton("🔙 Назад к управлению подписками", callback_data=ADMIN_CALLBACKS['admin_subscriptions'])]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        manage_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_admin_activate_trial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик активации триального периода"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    # Получаем Telegram ID из callback data
    if ':' in query.data:
        telegram_id = int(query.data.split(':')[1])
    else:
        await query.message.reply_text("❌ Ошибка: не удалось получить ID пользователя")
        return
    
    # Активируем триальный период
    success = activate_premium_subscription(telegram_id, 1)  # 1 день триала
    
    if success:
        await query.message.reply_text(
            f"✅ **Триальный период активирован!**\n\n"
            f"👤 Пользователь: {telegram_id}\n"
            f"🆓 Период: 1 день\n"
            f"📅 Истекает: завтра",
            parse_mode='Markdown'
        )
    else:
        await query.message.reply_text(
            f"❌ **Ошибка активации триального периода!**\n\n"
            f"Пользователь {telegram_id} не найден или произошла ошибка базы данных.",
            parse_mode='Markdown'
        )

async def handle_admin_activate_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик активации премиум подписки"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    # Получаем Telegram ID из callback data
    if ':' in query.data:
        telegram_id = int(query.data.split(':')[1])
    else:
        await query.message.reply_text("❌ Ошибка: не удалось получить ID пользователя")
        return
    
    # Активируем премиум подписку
    success = activate_premium_subscription(telegram_id, 30)  # 30 дней премиум
    
    if success:
        await query.message.reply_text(
            f"✅ **Премиум подписка активирована!**\n\n"
            f"👤 Пользователь: {telegram_id}\n"
            f"⭐ Период: 30 дней\n"
            f"📅 Истекает: через 30 дней",
            parse_mode='Markdown'
        )
    else:
        await query.message.reply_text(
            f"❌ **Ошибка активации премиум подписки!**\n\n"
            f"Пользователь {telegram_id} не найден или произошла ошибка базы данных.",
            parse_mode='Markdown'
        )

async def handle_admin_deactivate_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик деактивации подписки"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    # Получаем Telegram ID из callback data
    if ':' in query.data:
        telegram_id = int(query.data.split(':')[1])
    else:
        await query.message.reply_text("❌ Ошибка: не удалось получить ID пользователя")
        return
    
    # Деактивируем подписку (устанавливаем как истекшую)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET subscription_type = 'trial_expired',
                    is_premium = 0,
                    subscription_expires_at = datetime('now', '-1 day')
                WHERE telegram_id = ?
            ''', (telegram_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                await query.message.reply_text(
                    f"✅ **Подписка деактивирована!**\n\n"
                    f"👤 Пользователь: {telegram_id}\n"
                    f"❌ Статус: Подписка отменена",
                    parse_mode='Markdown'
                )
            else:
                await query.message.reply_text(
                    f"❌ **Ошибка деактивации подписки!**\n\n"
                    f"Пользователь {telegram_id} не найден.",
                    parse_mode='Markdown'
                )
    except Exception as e:
        logger.error(f"Error deactivating subscription: {e}")
        await query.message.reply_text(
            f"❌ **Ошибка деактивации подписки!**\n\n"
            f"Произошла ошибка базы данных.",
            parse_mode='Markdown'
        )

async def handle_admin_telegram_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода Telegram ID для админки"""
    user = update.effective_user
    
    # Проверяем права админа
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    text = update.message.text.strip()
    
    try:
        # Пытаемся преобразовать в число
        telegram_id = int(text)
        
        # Проверяем, что это положительное число
        if telegram_id <= 0:
            await update.message.reply_text("❌ Telegram ID должен быть положительным числом!")
            return
        
        # Проверяем, существует ли пользователь
        user_data = get_user_by_telegram_id(telegram_id)
        if not user_data:
            await update.message.reply_text(
                f"❌ **Пользователь не найден!**\n\n"
                f"🆔 Telegram ID: {telegram_id}\n"
                f"Пользователь не зарегистрирован в боте.",
                parse_mode='Markdown'
            )
            # Сбрасываем состояние ожидания
            context.user_data['admin_waiting_for_telegram_id'] = False
            return
        
        # Сбрасываем состояние ожидания
        context.user_data['admin_waiting_for_telegram_id'] = False
        
        # Показываем меню управления подпиской
        await show_admin_manage_subscription_menu(update, context, telegram_id, user_data)
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Неверный формат Telegram ID!**\n\n"
            "Пожалуйста, введите числовой ID пользователя (например: 123456789)",
            parse_mode='Markdown'
        )

async def show_admin_manage_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id: int, user_data: Optional[Tuple[Any, ...]]):
    """Показывает меню управления подпиской для конкретного пользователя"""
    # Получаем информацию о подписке
    subscription_info = check_user_subscription(telegram_id)
    
    # Формируем текст о подписке
    subscription_text = ""
    if subscription_info['is_active']:
        if subscription_info['type'] == 'trial':
            subscription_text = f"🆓 **Триальный период**\nДоступен до: {subscription_info['expires_at']}"
        elif subscription_info['type'] == 'premium':
            if subscription_info['expires_at']:
                subscription_text = f"⭐ **Премиум подписка**\nДействует до: {subscription_info['expires_at']}"
            else:
                subscription_text = "⭐ **Премиум подписка**\nБез ограничений"
    else:
        if subscription_info['type'] == 'trial_expired':
            subscription_text = f"❌ **Триальный период истек**\nИстек: {subscription_info['expires_at']}"
        elif subscription_info['type'] == 'premium_expired':
            subscription_text = f"❌ **Премиум подписка истекла**\nИстекла: {subscription_info['expires_at']}"
        else:
            subscription_text = "❌ **Нет активной подписки**"
    
    manage_text = f"""
👤 **Управление подпиской пользователя**

📝 **Имя:** {user_data[2]}
🆔 **Telegram ID:** {telegram_id}
📅 **Дата регистрации:** {user_data[9]}

{subscription_text}

Выберите действие:
    """
    
    keyboard = [
        [InlineKeyboardButton("🆓 Активировать триал (1 день)", callback_data=f"{ADMIN_CALLBACKS['admin_activate_trial']}:{telegram_id}")],
        [InlineKeyboardButton("⭐ Активировать премиум (30 дней)", callback_data=f"{ADMIN_CALLBACKS['admin_activate_premium']}:{telegram_id}")],
        [InlineKeyboardButton("❌ Деактивировать подписку", callback_data=f"{ADMIN_CALLBACKS['admin_deactivate_subscription']}:{telegram_id}")],
        [InlineKeyboardButton("🔙 Назад к управлению подписками", callback_data=ADMIN_CALLBACKS['admin_subscriptions'])]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        manage_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ==================== ФУНКЦИИ "УЗНАТЬ КАЛОРИИ" (БЕЗ СОХРАНЕНИЯ) ====================

async def handle_check_calories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Узнать калории' - сразу показывает интерфейс универсального анализа"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        user_data = check_user_registration(user.id)
        if not user_data:
            await query.edit_message_text(
                "❌ Вы не зарегистрированы в системе!\n"
                "Используйте /register для регистрации.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Проверяем подписку
        access_info = check_subscription_access(user.id)
        
        # Если подписка неактивна, проверяем лимит использований
        if not access_info['has_access']:
            daily_checks = get_daily_calorie_checks_count(user.id)
            if daily_checks >= 3:
                limit_msg = f"❌ **Лимит использований исчерпан**\n\n"
                limit_msg += f"Вы использовали функцию 'Узнать калории' {daily_checks}/3 раз сегодня.\n\n"
                limit_msg += f"⏰ **Счетчик сбрасывается в полночь**\n\n"
                limit_msg += f"💡 **Для неограниченного использования оформите подписку:**\n"
                limit_msg += f"• 1 день - 50 ⭐\n"
                limit_msg += f"• 7 дней - 200 ⭐\n"
                limit_msg += f"• 30 дней - 500 ⭐\n"
                limit_msg += f"• 90 дней - 1200 ⭐\n"
                limit_msg += f"• 365 дней - 4000 ⭐\n\n"
                limit_msg += f"💎 Безопасно • Мгновенно • Без комиссий"
                
                await query.edit_message_text(
                    limit_msg,
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='Markdown'
                )
                return
        
        # Устанавливаем режим проверки калорий для универсального анализа
        context.user_data['check_mode'] = True
        
        message_text = "🔍 **Универсальный анализ еды**\n\n"
        message_text += "Отправьте любое из следующего:\n"
        message_text += "• 📷 **Фото** блюда\n"
        message_text += "• 📝 **Текстовое описание** блюда\n"
        message_text += "• 🎤 **Голосовое сообщение** с описанием\n\n"
        message_text += "**Примеры описаний:**\n"
        message_text += "• \"Большая тарелка борща с мясом и сметаной\"\n"
        message_text += "• \"2 куска пиццы Маргарита среднего размера\"\n"
        message_text += "• \"Салат Цезарь с курицей и сыром пармезан\"\n\n"
        message_text += "ℹ️ **Результат будет показан, но НЕ сохранится в вашу статистику**"
        
        # Показываем информацию о лимите для пользователей без подписки
        if not access_info['has_access']:
            daily_checks = get_daily_calorie_checks_count(user.id)
            message_text += f"\n\n🆓 **Осталось использований: {3 - daily_checks}/3**"
            message_text += f"\n\n⏰ **Счетчик сбрасывается в полночь**"
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
            ]),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in handle_check_calories: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

async def handle_check_photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Анализ по фото' для проверки калорий"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем подписку и лимит использований
    access_info = check_subscription_access(user.id)
    if not access_info['has_access']:
        daily_checks = get_daily_calorie_checks_count(user.id)
        if daily_checks >= 3:
            limit_msg = f"❌ **Лимит использований исчерпан**\n\n"
            limit_msg += f"Вы использовали функцию 'Узнать калории' {daily_checks}/3 раз сегодня.\n\n"
            limit_msg += f"⏰ **Счетчик сбрасывается в полночь**\n\n"
            limit_msg += f"💡 **Для неограниченного использования оформите подписку:**\n"
            limit_msg += f"• 1 день - 50 ⭐\n"
            limit_msg += f"• 7 дней - 200 ⭐\n"
            limit_msg += f"• 30 дней - 500 ⭐\n"
            limit_msg += f"• 90 дней - 1200 ⭐\n"
            limit_msg += f"• 365 дней - 4000 ⭐\n\n"
            limit_msg += f"💎 Безопасно • Мгновенно • Без комиссий"
            
            await query.edit_message_text(
                limit_msg,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            return
    
    await query.message.reply_text(
        "📷 **Анализ по фото**\n\n"
        "Отправьте фотографию еды для анализа калорий.\n\n"
        "ℹ️ **Результат будет показан, но НЕ сохранится в статистику**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]),
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние ожидания фото для проверки
    context.user_data['waiting_for_check_photo'] = True
    context.user_data['check_mode'] = True

async def handle_check_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Анализ по тексту' для проверки калорий"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем подписку и лимит использований
    access_info = check_subscription_access(user.id)
    if not access_info['has_access']:
        daily_checks = get_daily_calorie_checks_count(user.id)
        if daily_checks >= 3:
            limit_msg = f"❌ **Лимит использований исчерпан**\n\n"
            limit_msg += f"Вы использовали функцию 'Узнать калории' {daily_checks}/3 раз сегодня.\n\n"
            limit_msg += f"⏰ **Счетчик сбрасывается в полночь**\n\n"
            limit_msg += f"💡 **Для неограниченного использования оформите подписку:**\n"
            limit_msg += f"• 1 день - 50 ⭐\n"
            limit_msg += f"• 7 дней - 200 ⭐\n"
            limit_msg += f"• 30 дней - 500 ⭐\n"
            limit_msg += f"• 90 дней - 1200 ⭐\n"
            limit_msg += f"• 365 дней - 4000 ⭐\n\n"
            limit_msg += f"💎 Безопасно • Мгновенно • Без комиссий"
            
            await query.edit_message_text(
                limit_msg,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            return
    
    await query.message.reply_text(
        "📝 **Анализ по тексту**\n\n"
        "Опишите блюдо для анализа калорий.\n\n"
        "ℹ️ **Результат будет показан, но НЕ сохранится в статистику**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]),
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние ожидания текста для проверки
    context.user_data['waiting_for_check_text'] = True
    context.user_data['check_mode'] = True

async def handle_check_voice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Анализ по голосу' для проверки калорий"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем подписку и лимит использований
    access_info = check_subscription_access(user.id)
    if not access_info['has_access']:
        daily_checks = get_daily_calorie_checks_count(user.id)
        if daily_checks >= 3:
            limit_msg = f"❌ **Лимит использований исчерпан**\n\n"
            limit_msg += f"Вы использовали функцию 'Узнать калории' {daily_checks}/3 раз сегодня.\n\n"
            limit_msg += f"⏰ **Счетчик сбрасывается в полночь**\n\n"
            limit_msg += f"💡 **Для неограниченного использования оформите подписку:**\n"
            limit_msg += f"• 1 день - 50 ⭐\n"
            limit_msg += f"• 7 дней - 200 ⭐\n"
            limit_msg += f"• 30 дней - 500 ⭐\n"
            limit_msg += f"• 90 дней - 1200 ⭐\n"
            limit_msg += f"• 365 дней - 4000 ⭐\n\n"
            limit_msg += f"💎 Безопасно • Мгновенно • Без комиссий"
            
            await query.edit_message_text(
                limit_msg,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            return
    
    await query.message.reply_text(
        "🎤 **Анализ по голосу**\n\n"
        "Отправьте голосовое сообщение с описанием блюда для анализа калорий.\n\n"
        "ℹ️ **Результат будет показан, но НЕ сохранится в статистику**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]),
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние ожидания голоса для проверки
    context.user_data['waiting_for_check_voice'] = True
    context.user_data['check_mode'] = True

async def analyze_food_photo(image_data: bytes):
    """Анализирует фотографию еды с помощью API"""
    try:
        # Валидация входных данных
        if not image_data or not isinstance(image_data, bytes):
            logger.error("Invalid image data provided")
            return None
        
        if len(image_data) < 100:  # Минимальный размер изображения
            logger.error("Image data too small")
            return None
            
        logger.info("Starting food photo analysis...")
        
        async with APIClient() as client:
            result = await client.analyze_image(image_data)
            
            if result:
                logger.info(f"Photo analysis successful, result length: {len(result)}")
                return result
            else:
                logger.error("Photo analysis failed - no result returned")
                return None
                
    except Exception as e:
        logger.error(f"Error in food photo analysis: {e}")
        return None

async def analyze_food_text(description: str):
    """Анализирует текстовое описание блюда с помощью API"""
    try:
        # Валидация входных данных
        if not description or not isinstance(description, str):
            logger.error("Invalid description provided")
            return None
        
        if len(description.strip()) < 5:
            logger.error("Description too short")
            return None
            
        logger.info("Starting food text analysis...")
        
        async with api_client:
            result = await api_client.analyze_text(description)
            
            if result:
                logger.info(f"Text analysis successful, result length: {len(result)}")
                return result
            else:
                logger.error("Text analysis failed - no result returned")
                return None
                
    except Exception as e:
        logger.error(f"Error in food text analysis: {e}")
        return None

async def transcribe_voice(audio_data: bytes):
    """Распознает речь из аудиофайла с помощью API"""
    try:
        # Валидация входных данных
        if not audio_data or not isinstance(audio_data, bytes):
            logger.error("Invalid audio data provided")
            return None
        
        if len(audio_data) < 1000:  # Минимальный размер аудио
            logger.error("Audio data too small")
            return None
            
        logger.info("Starting voice transcription...")
        
        async with api_client:
            result = await api_client.analyze_voice(audio_data)
            
            if result:
                logger.info(f"Voice transcription successful, result length: {len(result)}")
                return result.strip()
            else:
                logger.error("Voice transcription failed - no result returned")
                return None
                
    except Exception as e:
        logger.error(f"Error in voice transcription: {e}")
        return None


async def handle_meal_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора приема пищи"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Определяем тип приема пищи
    meal_types = {
        'meal_breakfast': '🌅 Завтрак',
        'meal_lunch': '☀️ Обед', 
        'meal_dinner': '🌙 Ужин',
        'meal_snack': '🍎 Перекус'
    }
    
    meal_name = meal_types.get(query.data, 'Прием пищи')
    
    # Сохраняем выбранный прием пищи в контексте
    context.user_data['selected_meal'] = query.data
    context.user_data['selected_meal_name'] = meal_name
    
    # Устанавливаем режим сохранения для автоматического анализа
    context.user_data['save_mode'] = True
    
    # Создаем клавиатуру с кнопкой "назад в меню"
    keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Автоматически вызываем команду анализа с сохранением
    await query.edit_message_text(
        f"🍽️ **{meal_name}**\n\n"
        "🤖 **Анализ еды с сохранением**\n\n"
        "Отправьте мне:\n"
        "• 📷 **Фото еды** - для анализа изображения\n"
        "• 📝 **Текстовое описание** - для анализа текста\n"
        "• 🎤 **Голосовое сообщение** - для анализа речи\n\n"
        "Результат будет автоматически сохранен в вашу статистику!\n\n"
        "**Примеры:**\n"
        "• \"Борщ с мясом, 300г\"\n"
        "• \"Салат Цезарь с курицей\"\n"
        "• \"Пицца Маргарита, 2 куска\"",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_analyze_photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Анализ по фото'"""
    query = update.callback_query
    await query.answer()
    
    # Устанавливаем состояние ожидания фото
    context.user_data['waiting_for_photo'] = True
    
    # Получаем информацию о выбранном приеме пищи
    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
    
    await query.edit_message_text(
        f"📸 **Анализ фотографии еды - {selected_meal}**\n\n"
        "Пришлите мне фото блюда, калорийность которого вы хотите оценить.\n\n"
        "⚠️ **Для более точного расчета на фото должны присутствовать якорные объекты:**\n"
        "• Вилка\n"
        "• Ложка\n"
        "• Рука\n"
        "• Монета\n"
        "• Другие объекты для масштаба\n\n"
        "Модель проанализирует фото и вернет:\n"
        "• Название блюда\n"
        "• Ориентировочный вес\n"
        "• Калорийность\n"
        "• Раскладку по БЖУ",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_analysis")],
            [InlineKeyboardButton("🔙 Назад к приемам пищи", callback_data="add_dish")]
        ]),
        parse_mode='Markdown'
    )

async def handle_analyze_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Анализ по тексту'"""
    query = update.callback_query
    await query.answer()
    
    # Устанавливаем состояние ожидания текстового описания
    context.user_data['waiting_for_text'] = True
    
    # Получаем информацию о выбранном приеме пищи
    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
    
    await query.edit_message_text(
        f"📝 **Анализ описания блюда - {selected_meal}**\n\n"
        "Опишите блюдо, калорийность которого вы хотите оценить.\n\n"
        "**Примеры описаний:**\n"
        "• \"Большая тарелка борща с мясом и сметаной\"\n"
        "• \"2 куска пиццы Маргарита среднего размера\"\n"
        "• \"Салат Цезарь с курицей и сыром пармезан\"\n"
        "• \"Порция жареной картошки с луком\"\n\n"
        "**Укажите:**\n"
        "• Название блюда\n"
        "• Примерный размер порции\n"
        "• Основные ингредиенты\n\n"
        "Модель проанализирует описание и вернет:\n"
        "• Название блюда\n"
        "• Ориентировочный вес\n"
        "• Калорийность\n"
        "• Раскладку по БЖУ",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_analysis")],
            [InlineKeyboardButton("🔙 Назад к приемам пищи", callback_data="add_dish")]
        ]),
        parse_mode='Markdown'
    )

async def handle_analyze_voice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Анализ по голосовому'"""
    query = update.callback_query
    await query.answer()
    
    # Устанавливаем состояние ожидания голосового сообщения
    context.user_data['waiting_for_voice'] = True
    
    # Получаем информацию о выбранном приеме пищи
    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
    
    await query.edit_message_text(
        f"🎤 **Анализ голосового описания блюда - {selected_meal}**\n\n"
        "Отправьте голосовое сообщение с описанием блюда, калорийность которого вы хотите оценить.\n\n"
        "**Примеры описаний:**\n"
        "• \"Большая тарелка борща с мясом и сметаной\"\n"
        "• \"Два куска пиццы Маргарита среднего размера\"\n"
        "• \"Салат Цезарь с курицей и сыром пармезан\"\n"
        "• \"Порция жареной картошки с луком\"\n\n"
        "**Укажите в голосовом сообщении:**\n"
        "• Название блюда\n"
        "• Примерный размер порции\n"
        "• Основные ингредиенты\n\n"
        "Модель проанализирует голосовое сообщение и вернет:\n"
        "• Название блюда\n"
        "• Ориентировочный вес\n"
        "• Калорийность\n"
        "• Раскладку по БЖУ",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_analysis")],
            [InlineKeyboardButton("🔙 Назад к приемам пищи", callback_data="add_dish")]
        ]),
        parse_mode='Markdown'
    )

async def handle_analyze_photo_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Фото + Текст' для добавления блюда"""
    query = update.callback_query
    await query.answer()
    
    # Устанавливаем состояние ожидания фото
    context.user_data['waiting_for_photo_text'] = True
    
    # Получаем информацию о выбранном приеме пищи
    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
    
    await query.edit_message_text(
        f"📷📝 **Комбинированный анализ блюда - {selected_meal}**\n\n"
        "**Шаг 1:** Отправьте фото блюда\n\n"
        "**Шаг 2:** После анализа фото отправьте текстовое описание с уточнениями:\n"
        "• Размер порции (\"большая тарелка\", \"2 куска\", \"примерно 300г\")\n"
        "• Дополнительные ингредиенты (\"с добавлением сыра\", \"без масла\")\n"
        "• Способ приготовления (\"домашний рецепт\", \"жареное\")\n\n"
        "**Примеры уточнений:**\n"
        "• \"Большая порция, диаметр 30см, с добавлением моцареллы\"\n"
        "• \"2 куска, домашний рецепт, без масла\"\n"
        "• \"Примерно 250г, с двойной порцией мяса\"\n\n"
        "⚠️ **Для более точного расчета на фото должны присутствовать якорные объекты:**\n"
        "• Вилка, ложка, рука, монета или другие объекты для масштаба\n\n"
        "Модель проанализирует и фото, и текст для максимально точного результата!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_analysis")],
            [InlineKeyboardButton("🔙 Назад к приемам пищи", callback_data="add_dish")]
        ]),
        parse_mode='Markdown'
    )


async def handle_cancel_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Отмена' для отмены анализа"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем все состояния ожидания
    context.user_data.pop('waiting_for_photo', None)
    context.user_data.pop('waiting_for_text', None)
    context.user_data.pop('waiting_for_voice', None)
    context.user_data.pop('waiting_for_photo_text', None)
    context.user_data.pop('waiting_for_check_photo', None)
    context.user_data.pop('waiting_for_check_text', None)
    context.user_data.pop('waiting_for_check_voice', None)
    context.user_data.pop('waiting_for_check_photo_text', None)
    context.user_data.pop('waiting_for_text_after_photo', None)
    context.user_data.pop('waiting_for_check_text_after_photo', None)
    
    # Очищаем временные данные анализа
    context.user_data.pop('photo_analysis_result', None)
    context.user_data.pop('photo_dish_name', None)
    context.user_data.pop('photo_calories', None)
    
    # Показываем главное меню
    await query.edit_message_text(
        "🏠 **Главное меню**\n\n"
        "Выберите нужную функцию:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )


async def handle_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Назад в меню'"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🏠 **Главное меню**\n\n"
        "Выберите нужную функцию:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def handle_statistics_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Статистика'"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем подписку
    access_info = check_subscription_access(user.id)
    if not access_info['has_access']:
        subscription_msg = get_subscription_message(access_info)
        await query.edit_message_text(
            subscription_msg,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    try:
        # Получаем информацию о пользователе
        user_data = check_user_registration(user.id)
        if not user_data:
            await query.edit_message_text(
                "❌ Вы не зарегистрированы в системе!\n"
                "Используйте /register для регистрации.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Создаем подменю для выбора периода
        keyboard = [
            [InlineKeyboardButton("📅 За сегодня", callback_data="stats_today")],
            [InlineKeyboardButton("📅 За вчера", callback_data="stats_yesterday")],
            [InlineKeyboardButton("📅 За неделю", callback_data="stats_week")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📊 **Статистика**\n\n"
            "Выберите период для просмотра статистики:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing statistics menu: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении статистики. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

async def handle_stats_today_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'За сегодня'"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Получаем статистику по приемам пищи за сегодня
        daily_meals = get_daily_meals_by_type(user.id)
        
        # Формируем сообщение со статистикой
        stats_text = "📊 **Ваша статистика за сегодня:**\n\n"
        
        # Определяем порядок приемов пищи
        meal_order = [
            ('meal_breakfast', '🌅 Завтрак'),
            ('meal_lunch', '☀️ Обед'),
            ('meal_dinner', '🌙 Ужин'),
            ('meal_snack', '🍎 Перекус')
        ]
        
        total_calories = 0
        
        for meal_type, meal_name in meal_order:
            if meal_type in daily_meals:
                calories = daily_meals[meal_type]['calories']
                total_calories += calories
                stats_text += f"{meal_name} - {calories} калорий\n"
            else:
                stats_text += f"{meal_name} - 0 калорий\n"
        
        stats_text += f"\n🔥 **Всего за день:** {total_calories} калорий"
        
        # Добавляем процент от суточной нормы и от цели
        try:
            # Получаем данные пользователя для расчета суточной нормы
            user_data = get_user_by_telegram_id(user.id)
            if user_data:
                daily_norm = calculate_daily_calories(
                    user_data['age'], 
                    user_data['height'], 
                    user_data['weight'], 
                    user_data['gender'], 
                    user_data['activity_level']
                )
                percentage = round((total_calories / daily_norm) * 100, 1)
                stats_text += f"\n📊 **Процент от суточной нормы:** {percentage}%"
                
                # Добавляем процент от цели
                goal = user_data[13] if len(user_data) > 13 else 'maintain'
                target_calories = int(user_data[14]) if len(user_data) > 14 and user_data[14] else daily_norm
                
                if target_calories > 0:
                    goal_percentage = round((total_calories / target_calories) * 100, 1)
                    goal_text = GOALS.get(goal, 'Держать себя в форме')
                    goal_emoji = "📉" if goal == 'lose_weight' else "⚖️" if goal == 'maintain' else "📈"
                    stats_text += f"\n🎯 **Процент от цели ({goal_emoji} {goal_text}):** {goal_percentage}%"
        except Exception as e:
            logger.error(f"Error calculating daily percentage: {e}")
        
        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton("🔙 Назад к статистике", callback_data="statistics")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing today's statistics: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении статистики. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к статистике", callback_data="statistics")]
            ])
        )

async def handle_stats_yesterday_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'За вчера'"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Получаем дату вчера
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Получаем статистику по приемам пищи за вчера
        daily_meals = get_daily_meals_by_type(user.id, yesterday)
        
        # Формируем сообщение со статистикой
        stats_text = "📊 **Ваша статистика за вчера:**\n\n"
        
        # Определяем порядок приемов пищи
        meal_order = [
            ('meal_breakfast', '🌅 Завтрак'),
            ('meal_lunch', '☀️ Обед'),
            ('meal_dinner', '🌙 Ужин'),
            ('meal_snack', '🍎 Перекус')
        ]
        
        total_calories = 0
        
        for meal_type, meal_name in meal_order:
            if meal_type in daily_meals:
                calories = daily_meals[meal_type]['calories']
                total_calories += calories
                stats_text += f"{meal_name} - {calories} калорий\n"
            else:
                stats_text += f"{meal_name} - 0 калорий\n"
        
        stats_text += f"\n🔥 **Всего за день:** {total_calories} калорий"
        
        # Добавляем процент от суточной нормы и от цели
        try:
            # Получаем данные пользователя для расчета суточной нормы
            user_data = get_user_by_telegram_id(user.id)
            if user_data:
                daily_norm = calculate_daily_calories(
                    user_data['age'], 
                    user_data['height'], 
                    user_data['weight'], 
                    user_data['gender'], 
                    user_data['activity_level']
                )
                percentage = round((total_calories / daily_norm) * 100, 1)
                stats_text += f"\n📊 **Процент от суточной нормы:** {percentage}%"
                
                # Добавляем процент от цели
                goal = user_data[13] if len(user_data) > 13 else 'maintain'
                target_calories = int(user_data[14]) if len(user_data) > 14 and user_data[14] else daily_norm
                
                if target_calories > 0:
                    goal_percentage = round((total_calories / target_calories) * 100, 1)
                    goal_text = GOALS.get(goal, 'Держать себя в форме')
                    goal_emoji = "📉" if goal == 'lose_weight' else "⚖️" if goal == 'maintain' else "📈"
                    stats_text += f"\n🎯 **Процент от цели ({goal_emoji} {goal_text}):** {goal_percentage}%"
        except Exception as e:
            logger.error(f"Error calculating daily percentage: {e}")
        
        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton("🔙 Назад к статистике", callback_data="statistics")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing yesterday's statistics: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении статистики. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к статистике", callback_data="statistics")]
            ])
        )

async def handle_stats_week_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'За неделю'"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Получаем статистику за неделю
        week_stats = get_weekly_meals_by_type(user.id)
        
        # Формируем сообщение со статистикой
        stats_text = "📊 **Ваша статистика за неделю:**\n\n"
        
        # Определяем порядок дней недели
        days_order = [
            'Понедельник', 'Вторник', 'Среда', 'Четверг', 
            'Пятница', 'Суббота', 'Воскресенье'
        ]
        
        total_week_calories = 0
        
        for day in days_order:
            if day in week_stats:
                calories = week_stats[day]
                total_week_calories += calories
                stats_text += f"{day} - {calories} калорий\n"
            else:
                stats_text += f"{day} - 0 калорий\n"
        
        stats_text += f"\n🔥 **Всего за неделю:** {total_week_calories} калорий"
        
        # Добавляем процент от суточной нормы и от цели
        try:
            # Получаем данные пользователя для расчета суточной нормы
            user_data = get_user_by_telegram_id(user.id)
            if user_data:
                daily_norm = calculate_daily_calories(
                    user_data['age'], 
                    user_data['height'], 
                    user_data['weight'], 
                    user_data['gender'], 
                    user_data['activity_level']
                )
                weekly_norm = daily_norm * 7
                percentage = round((total_week_calories / weekly_norm) * 100, 1)
                stats_text += f"\n📊 **Процент от недельной нормы:** {percentage}%"
                
                # Добавляем процент от цели
                goal = user_data[10] if len(user_data) > 10 else 'maintain'
                target_calories = user_data[11] if len(user_data) > 11 else daily_norm
                weekly_target = target_calories * 7
                
                if weekly_target > 0:
                    goal_percentage = round((total_week_calories / weekly_target) * 100, 1)
                    goal_text = GOALS.get(goal, 'Держать себя в форме')
                    goal_emoji = "📉" if goal == 'lose_weight' else "⚖️" if goal == 'maintain' else "📈"
                    stats_text += f"\n🎯 **Процент от недельной цели ({goal_emoji} {goal_text}):** {goal_percentage}%"
        except Exception as e:
            logger.error(f"Error calculating weekly percentage: {e}")
        
        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton("🔙 Назад к статистике", callback_data="statistics")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing week's statistics: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении статистики. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к статистике", callback_data="statistics")]
            ])
        )

async def show_meal_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику приемов пищи пользователя"""
    user = update.effective_user
    
    try:
        # Получаем статистику за сегодня
        daily_stats = get_daily_calories(user.id)
        
        # Получаем статистику за последние 7 дней
        weekly_stats = get_meal_statistics(user.id, 7)
        
        # Получаем информацию о пользователе
        user_data = check_user_registration(user.id)
        if not user_data:
            await update.message.reply_text(
                "❌ Вы не зарегистрированы в системе!\n"
                "Используйте /register для регистрации."
            )
            return
        
        daily_calories = user_data[8]  # Суточная норма калорий
        consumed_calories = daily_stats['total_calories']
        remaining_calories = daily_calories - consumed_calories
        progress_percent = (consumed_calories / daily_calories * 100) if daily_calories > 0 else 0
        
        # Формируем сообщение со статистикой
        stats_text = f"""
📊 **Ваша статистика питания**

📅 **Сегодня ({daily_stats['meals_count']} приемов пищи):**
🔥 **Съедено:** {consumed_calories} ккал
🎯 **Норма:** {daily_calories} ккал
📈 **Осталось:** {remaining_calories} ккал
📊 **Прогресс:** {progress_percent:.1f}%

🍽️ **БЖУ за день:**
• Белки: {daily_stats['total_protein']:.1f}г
• Жиры: {daily_stats['total_fat']:.1f}г
• Углеводы: {daily_stats['total_carbs']:.1f}г

📈 **Статистика за неделю:**
"""
        
        # Добавляем статистику по дням
        for day_stat in weekly_stats[:5]:  # Показываем только последние 5 дней
            date_str = day_stat['date']
            day_calories = day_stat['daily_calories']
            meals_count = day_stat['meals_count']
            stats_text += f"• {date_str}: {day_calories} ккал ({meals_count} приемов)\n"
        
        if not weekly_stats:
            stats_text += "• Данных за неделю пока нет\n"
        
        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing meal statistics: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении статистики. Попробуйте позже."
        )

# ==================== ФУНКЦИИ ДЛЯ ОПЛАТЫ ПОДПИСКИ ====================

async def show_subscription_purchase_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню покупки подписки"""
    query = update.callback_query
    user = update.effective_user
    
    try:
        # Проверяем текущую подписку
        subscription_info = check_user_subscription(user.id)
        
        if subscription_info['is_active']:
            await query.edit_message_text(
                f"✅ У вас уже есть активная подписка!\n\n"
                f"📋 **Тип:** {subscription_info['type']}\n"
                f"⏰ **Истекает:** {subscription_info['expires_at']}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="profile")]
                ])
            )
            return
        
        # Создаем меню с одним вариантом подписки
        keyboard = [
            [InlineKeyboardButton(
                f"💎 {SUBSCRIPTION_DESCRIPTIONS['premium_7_days']}", 
                callback_data="buy_premium_7_days"
            )],
            [InlineKeyboardButton("🔙 Назад к профилю", callback_data="profile")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = """
💎 **Купить подписку**

🌟 **Оплата через Telegram Stars**
• Безопасно • Мгновенно • Без комиссий
• Работает по всему миру

📱 **Важно:** Оплата Stars доступна только в мобильном приложении Telegram

💡 Подписка дает полный доступ ко всем функциям бота
"""
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing subscription purchase menu: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при загрузке меню подписки. Попробуйте позже."
        )

async def handle_subscription_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает покупку подписки"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    subscription_type = query.data.replace('buy_', '')
    
    try:
        # Проверяем, что подписка существует
        if subscription_type not in SUBSCRIPTION_PRICES:
            await query.message.reply_text("❌ Неверный тип подписки.")
            return
        
        price = SUBSCRIPTION_PRICES[subscription_type]
        
        # Создаем инвойс для оплаты
        await create_payment_invoice(user.id, subscription_type, price, query, context)
        
    except Exception as e:
        logger.error(f"Error handling subscription purchase: {e}")
        await query.message.reply_text(
            "❌ Произошла ошибка при обработке покупки. Попробуйте позже."
        )

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

async def handle_pre_checkout_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает запрос перед оплатой"""
    query = update.pre_checkout_query
    
    try:
        # Проверяем, что у нас есть данные о платеже
        if 'pending_payment' not in context.user_data:
            await query.answer(ok=False, error_message="Данные о платеже не найдены")
            return
        
        payment_data = context.user_data['pending_payment']
        expected_price = payment_data['price']
        
        # Проверяем сумму платежа
        if query.invoice_payload != f"subscription_{payment_data['subscription_type']}":
            await query.answer(ok=False, error_message="Неверные данные платежа")
            return
        
        # Подтверждаем платеж
        await query.answer(ok=True)
        
    except Exception as e:
        logger.error(f"Error handling pre-checkout query: {e}")
        await query.answer(ok=False, error_message="Ошибка обработки платежа")

async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает успешную оплату"""
    payment = update.message.successful_payment
    
    try:
        # Получаем данные о платеже
        if 'pending_payment' not in context.user_data:
            await update.message.reply_text(
                "❌ Данные о платеже не найдены. Обратитесь к администратору."
            )
            return
        
        payment_data = context.user_data['pending_payment']
        user_id = payment_data['user_id']
        days = payment_data['days']
        subscription_type = payment_data['subscription_type']
        stars_amount = payment.total_amount // 100  # Конвертируем из копеек в Stars
        
        # Активируем подписку
        activate_premium_subscription(user_id, days)
        
        # Очищаем данные о платеже
        del context.user_data['pending_payment']
        
        # Получаем текущий баланс Stars бота
        try:
            balance_stars = await get_bot_star_balance()
            if balance_stars is None:
                balance_stars = "недоступен (требуется регистрация разработчика)"
        except Exception as e:
            logger.warning(f"Could not get star balance: {e}")
            balance_stars = "недоступен (требуется регистрация разработчика)"
        
        # Отправляем подтверждение
        success_message = f"🎉 **Оплата успешно завершена!**\n\n"
        success_message += f"✅ Подписка активирована на {days} дней\n"
        success_message += f"⏰ Истекает: {datetime.now() + timedelta(days=days):%d.%m.%Y %H:%M}\n"
        success_message += f"💎 Оплачено: {stars_amount} ⭐\n"
        success_message += f"💰 Баланс бота: {balance_stars} ⭐\n\n"
        success_message += f"💎 Теперь у вас есть доступ ко всем функциям бота!"
        
        await update.message.reply_text(
            success_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 К профилю", callback_data="profile")]
            ]),
            parse_mode='Markdown'
        )
        
        # Логируем успешный платеж
        logger.info(f"Successful payment: user {user_id}, subscription {subscription_type}, {days} days, {stars_amount} Stars, bot balance: {balance_stars}")
        
    except Exception as e:
        logger.error(f"Error handling successful payment: {e}")
        await update.message.reply_text(
            "❌ Ошибка активации подписки. Обратитесь к администратору."
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

async def handle_admin_star_balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Баланс Stars' в админке"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    try:
        # Получаем баланс Stars
        balance_stars = await get_bot_star_balance()
        
        if balance_stars is not None:
            # Конвертируем в доллары (примерно 1 Star = $0.01)
            usd_equivalent = balance_stars * 0.01
            
            balance_text = f"""
💎 **Баланс Telegram Stars**

💰 **Текущий баланс:** {balance_stars:,} ⭐
💵 **Примерно в долларах:** ${usd_equivalent:.2f}

📊 **Информация:**
• 70% от платежей поступает на баланс
• 30% комиссия Telegram
• Минимальная выплата: $100
• Выплаты ежемесячно

🔄 **Обновлено:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
            """
        else:
            balance_text = """
💎 **Баланс Telegram Stars**

❌ **Ошибка получения баланса**

Возможные причины:
• Бот не зарегистрирован как разработчик
• Проблемы с API Telegram
• Недостаточно прав

Попробуйте позже или обратитесь к поддержке.
            """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="admin_star_balance")],
            [InlineKeyboardButton("🔙 Админ панель", callback_data=ADMIN_CALLBACKS['admin_panel'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            balance_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in handle_admin_star_balance_callback: {e}")
        await query.message.reply_text(
            "❌ Произошла ошибка при получении баланса Stars. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Админ панель", callback_data=ADMIN_CALLBACKS['admin_panel'])]
            ])
        )


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Универсальная команда для анализа еды
    Автоматически определяет тип данных (фото, текст, голос) и вызывает соответствующую обработку
    """
    user = update.effective_user
    logger.info(f"Universal analyze command from user {user.id}")
    
    # Проверяем, зарегистрирован ли пользователь
    user_data = get_user_by_telegram_id(user.id)
    if not user_data:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы в системе!\n"
            "Используйте /register для регистрации.",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем подписку
    subscription = check_user_subscription(user.id)
    if not subscription['is_active']:
        await update.message.reply_text(
            "❌ У вас нет активной подписки!\n\n"
            "Используйте /subscription для покупки подписки.",
            parse_mode='Markdown'
        )
        return
    
    # Отправляем инструкцию
    message = """
🤖 **Универсальный анализ еды**

Отправьте мне:
• 📷 **Фото еды** - для анализа изображения
• 📝 **Текстовое описание** - для анализа текста  
• 🎤 **Голосовое сообщение** - для анализа речи

Я автоматически определю тип данных и проведу анализ!

**Примеры:**
• "Борщ с мясом, 300г"
• "Салат Цезарь с курицей"
• "Пицца Маргарита, 2 куска"
    """
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )


async def analyze_save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда для анализа еды с сохранением в базу данных
    Автоматически определяет тип данных (фото, текст, голос) и сохраняет результат
    """
    user = update.effective_user
    logger.info(f"Universal analyze save command from user {user.id}")
    
    # Проверяем, зарегистрирован ли пользователь
    user_data = get_user_by_telegram_id(user.id)
    if not user_data:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы в системе!\n"
            "Используйте /register для регистрации.",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем подписку
    subscription = check_user_subscription(user.id)
    if not subscription['is_active']:
        await update.message.reply_text(
            "❌ У вас нет активной подписки!\n\n"
            "Используйте /subscription для покупки подписки.",
            parse_mode='Markdown'
        )
        return
    
    # Отправляем инструкцию
    message = """
🤖 **Анализ еды с сохранением**

Отправьте мне:
• 📷 **Фото еды** - для анализа изображения
• 📝 **Текстовое описание** - для анализа текста  
• 🎤 **Голосовое сообщение** - для анализа речи

Результат будет автоматически сохранен в вашу статистику!

**Примеры:**
• "Борщ с мясом, 300г"
• "Салат Цезарь с курицей"
• "Пицца Маргарита, 2 куска"
    """
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
        )


async def handle_universal_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик универсального анализа
    Определяет тип данных и вызывает соответствующую функцию
    """
    user = update.effective_user
    message = update.message
    
    logger.info(f"Universal analysis from user {user.id}")
    
    # Проверяем, не ожидается ли ввод Telegram ID для админки
    if context.user_data.get('admin_waiting_for_telegram_id', False):
        logger.info(f"Admin waiting for telegram ID, redirecting to handle_text_input for user {user.id}")
        # Если ожидается ввод для админки, передаем управление handle_text_input
        await handle_text_input(update, context)
        return
    
    # Проверяем, не ожидается ли ввод текста для рассылки
    if context.user_data.get('waiting_for_broadcast_text', False):
        # Если ожидается ввод текста для рассылки, передаем управление handle_broadcast_text_input
        await handle_broadcast_text_input(update, context)
        return
    
    # Проверяем, не идет ли процесс регистрации
    if 'registration_step' in context.user_data:
        # Если идет регистрация, передаем управление handle_text_input
        await handle_text_input(update, context)
        return
    
    # Проверяем, зарегистрирован ли пользователь
    user_data = get_user_by_telegram_id(user.id)
    if not user_data:
        await message.reply_text(
            "❌ Вы не зарегистрированы в системе!\n"
            "Используйте /register для регистрации.",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем подписку только если не в режиме проверки калорий и пользователь не админ
    if not context.user_data.get('check_mode', False) and not is_admin(user.id):
        subscription = check_user_subscription(user.id)
        if not subscription['is_active']:
            await message.reply_text(
                "❌ У вас нет активной подписки!\n\n"
                "Используйте /subscription для покупки подписки.",
                parse_mode='Markdown'
            )
            return
    else:
        # В режиме проверки калорий проверяем лимит для пользователей без подписки (кроме админов)
        if not is_admin(user.id):
            subscription = check_user_subscription(user.id)
            if not subscription['is_active']:
                daily_checks = get_daily_calorie_checks_count(user.id)
                if daily_checks >= 3:
                    limit_msg = f"❌ **Лимит использований исчерпан**\n\n"
                    limit_msg += f"Вы использовали функцию 'Узнать калории' {daily_checks}/3 раз сегодня.\n\n"
                    limit_msg += f"⏰ **Счетчик сбрасывается в полночь**\n\n"
                    limit_msg += f"💡 **Для неограниченного использования оформите подписку:**\n"
                    limit_msg += f"• 1 день - 50 ⭐\n"
                    limit_msg += f"• 7 дней - 200 ⭐\n"
                    limit_msg += f"• 30 дней - 500 ⭐\n"
                    limit_msg += f"• 90 дней - 1200 ⭐\n"
                    limit_msg += f"• 365 дней - 4000 ⭐\n\n"
                    limit_msg += f"💎 Безопасно • Мгновенно • Без комиссий"
                
                    await message.reply_text(
                        limit_msg,
                        parse_mode='Markdown'
                    )
                    return
    
    # Определяем тип данных
    if message.photo:
        # Фото
        logger.info(f"Photo analysis for user {user.id}")
        if context.user_data.get('save_mode'):
            # Режим сохранения
            context.user_data['waiting_for_photo'] = True
        else:
            # Режим проверки калорий для команды /analyze
            context.user_data['check_mode'] = True
            context.user_data['waiting_for_check_photo'] = True
        await handle_photo(update, context)
        
    elif message.voice:
        # Голосовое сообщение
        logger.info(f"Voice analysis for user {user.id}")
        if context.user_data.get('save_mode'):
            # Режим сохранения
            context.user_data['waiting_for_voice'] = True
        else:
            # Режим проверки калорий для команды /analyze
            context.user_data['check_mode'] = True
            context.user_data['waiting_for_check_voice'] = True
        await handle_voice(update, context)
        
    elif message.text and not message.text.startswith('/'):
        # Текстовое описание
        logger.info(f"Text analysis for user {user.id}")
        if context.user_data.get('save_mode'):
            # Режим сохранения - устанавливаем флаг для автоматического сохранения
            context.user_data['auto_save'] = True
        else:
            # Режим проверки калорий для команды /analyze
            context.user_data['check_mode'] = True
        # Вызываем функцию анализа текста напрямую
        await handle_food_text_analysis(update, context)
        
    else:
        # Неподдерживаемый тип данных
        await message.reply_text(
            "❌ Неподдерживаемый тип данных!\n\n"
            "Отправьте:\n"
            "• 📷 Фото еды\n"
            "• 📝 Текстовое описание\n"
            "• 🎤 Голосовое сообщение",
            parse_mode='Markdown'
        )

