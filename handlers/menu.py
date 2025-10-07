"""
Модуль для обработки главного меню и навигации
"""
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_db_connection, check_user_subscription
from logging_config import get_logger

logger = get_logger(__name__)


# ==================== KEYBOARD BUILDERS ====================

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
    else:
        # Если user_id не передан, показываем кнопку "Купить подписку" по умолчанию
        keyboard.insert(3, [InlineKeyboardButton("⭐ Купить подписку", callback_data="subscription")])
    
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


# ==================== MENU DISPLAY ====================

async def show_welcome_message_with_data(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data):
    """Показывает приветственное сообщение с данными пользователя"""
    try:
        logger.info(f"show_welcome_message_with_data called with user_data length: {len(user_data)}")
        logger.info(f"user_data[17] (timezone): {user_data[17] if len(user_data) > 17 else 'N/A'}")
        logger.info(f"user_data[18] (reminders_enabled): {user_data[18] if len(user_data) > 18 else 'N/A'}")
        logger.info(f"user_data[19] (created_at): {user_data[19] if len(user_data) > 19 else 'N/A'}")
        
        # Получаем данные пользователя
        name = user_data[2]
        gender = user_data[3]
        age = user_data[4]
        height = user_data[5]
        weight = user_data[6]
        activity_level = user_data[7]
        goal = user_data[9]
        daily_calories = user_data[8]
        target_calories = user_data[10]
        # Правильные индексы для БЖУ: user_data[11] = target_protein, user_data[12] = target_fat, user_data[13] = target_carbs
        target_protein = user_data[11] if len(user_data) > 11 else 0.0
        target_fat = user_data[12] if len(user_data) > 12 else 0.0
        target_carbs = user_data[13] if len(user_data) > 13 else 0.0
        
        # Преобразуем в числа, если они строки
        try:
            target_protein = float(target_protein) if target_protein else 0.0
            target_fat = float(target_fat) if target_fat else 0.0
            target_carbs = float(target_carbs) if target_carbs else 0.0
        except (ValueError, TypeError):
            target_protein = 0.0
            target_fat = 0.0
            target_carbs = 0.0
        
        # Форматируем цель
        goal_emojis = {
            'lose_weight': '📉 Похудеть',
            'maintain': '⚖️ Держать себя в форме',
            'gain_weight': '📈 Набрать вес'
        }
        goal_text = goal_emojis.get(goal, goal)
        
        # Формируем приветственное сообщение
        welcome_message = f"""Привет {name}! ✅ Регистрация завершена!

🎯 Ваша цель: {goal_text}
📊 Расчетная норма: {daily_calories} ккал
🎯 Целевая норма: {target_calories} ккал

🥗 Суточная норма БЖУ:
• Белки: {target_protein:.1f}г
• Жиры: {target_fat:.1f}г
• Углеводы: {target_carbs:.1f}г

Выберите действие:"""
        
        # Показываем сообщение с главным меню
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                welcome_message,
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
        else:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                welcome_message,
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error showing welcome message: {e}")
        # Fallback to main menu
        await show_main_menu(update, context)


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


# ==================== COMMAND HANDLERS ====================

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
            # Пользователь зарегистрирован - показываем приветственное сообщение с данными
            await show_welcome_message_with_data(update, context, user_data)
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
/terms - Условия подписки
/dayreset - Сбросить данные за сегодня
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

**⭐ ПРЕМИУМ ПОДПИСКА:**
• Неограниченные анализы еды
• Детальная статистика калорий
• Персональные рекомендации
• Экспорт данных
• Поддержка 24/7

**💎 ЦЕНЫ:**
• 7 дней - 10 Telegram Stars

**🌟 Оплата через Telegram Stars:**
• Безопасно
• Мгновенно
• Без комиссий

**📝 УСЛОВИЯ:**
1. Подписка активируется автоматически после оплаты
2. Автопродление отсутствует
3. Возврат средств невозможен после активации
4. Поддержка: @calorigram_support

**🔐 КОНФИДЕНЦИАЛЬНОСТЬ:**
• Данные хранятся в зашифрованном виде
• Не передаются третьим лицам
• Удаляются по запросу пользователя
    """
    
    # Проверяем, это команда или callback запрос
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            terms_text,
            reply_markup=get_main_menu_keyboard_for_user(update),
            parse_mode='Markdown'
        )
    elif hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            terms_text,
            reply_markup=get_main_menu_keyboard_for_user(update),
            parse_mode='Markdown'
        )


# ==================== NAVIGATION HANDLERS ====================

async def handle_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик возврата в главное меню"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем все состояния
    context.user_data.clear()
    
    await show_main_menu(update, context)


async def handle_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопки главного меню"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем все состояния
    context.user_data.clear()
    
    await show_main_menu(update, context)


async def handle_menu_from_meal_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в меню из выбора типа приема пищи"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем состояния
    context.user_data.pop('selected_meal', None)
    context.user_data.pop('selected_meal_name', None)
    context.user_data.pop('save_mode', None)
    context.user_data.pop('check_mode', None)
    
    await show_main_menu(update, context)


async def handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопки помощи"""
    await help_command(update, context)


async def handle_terms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопки условий подписки"""
    await terms_command(update, context)

