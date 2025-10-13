# Auto-generated module for misc handlers extracted from bot_functions.py
from ._shared import *  # imports, constants, helpers
import bot_functions as bf  # for cross-module handler calls
from logging_config import get_logger
from handlers.registration import check_user_registration, validate_age, validate_height, validate_weight
from handlers.admin import is_admin
from handlers.subscription import check_subscription_access
from handlers.menu import get_main_menu_keyboard, get_main_menu_keyboard_for_user, get_analysis_result_keyboard
from handlers.media import handle_photo_with_text
from services.food_analysis_service import (
    analyze_food_text, 
    analyze_food_supplement,
    is_valid_analysis, 
    remove_explanations_from_analysis, 
    extract_calories_from_analysis,
    extract_macros_from_analysis,
    extract_weight_from_description,
    extract_calories_per_100g_from_analysis,
    extract_dish_name_from_analysis,
    clean_markdown_text
)
from database import get_user_by_telegram_id, check_user_subscription, get_daily_calorie_checks_count, add_meal, add_calorie_check, get_daily_calories
from constants import MIN_AGE, MAX_AGE, MIN_HEIGHT, MAX_HEIGHT, MIN_WEIGHT, MAX_WEIGHT

logger = get_logger(__name__)

__all__ = []

async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /terms - условия подписки"""
    return await terms_command_from_handler(update, context)

__all__.append('terms_command')

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

__all__.append('register_command')

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений для регистрации и анализа блюд"""
    user = update.effective_user
    
    # Проверяем, ожидается ли ввод Telegram ID для админки
    if context.user_data.get('admin_waiting_for_telegram_id', False):
        await bf.handle_admin_telegram_id_input(update, context)
        return
    
    # Проверяем, ожидается ли текстовое описание блюда
    if (context.user_data.get('waiting_for_text', False) or 
        context.user_data.get('waiting_for_check_text', False) or
        context.user_data.get('waiting_for_text_after_photo', False) or
        context.user_data.get('waiting_for_check_text_after_photo', False)):
        await bf.handle_food_text_analysis(update, context)
        return
    
    # Проверяем, ожидается ли дополнительный текст для дополнения анализа
    waiting_for_additional = context.user_data.get('waiting_for_additional_text', False)
    waiting_for_check_additional = context.user_data.get('waiting_for_check_additional_text', False)
    
    logger.info(f"Text input for user {user.id}: waiting_for_additional_text={waiting_for_additional}, waiting_for_check_additional_text={waiting_for_check_additional}")
    
    if waiting_for_additional:
        logger.info(f"Handling additional text analysis for user {user.id}")
        await bf.handle_additional_text_analysis(update, context)
        return
    
    if waiting_for_check_additional:
        logger.info(f"Handling check additional text analysis for user {user.id}")
        await bf.handle_check_additional_text_analysis(update, context)
        return
    
    # Отладочная информация
    logger.info(f"Text input for user {user.id}: waiting_for_additional_text={context.user_data.get('waiting_for_additional_text', False)}, waiting_for_check_additional_text={context.user_data.get('waiting_for_check_additional_text', False)}")
    logger.info(f"All user_data flags: {[k for k, v in context.user_data.items() if 'waiting' in k or 'additional' in k]}")
    
    # Проверяем, ожидается ли текст рассылки
    if context.user_data.get('waiting_for_broadcast_text', False):
        await bf.handle_broadcast_text_input(update, context)
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

__all__.append('handle_text_input')

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

__all__.append('handle_activity_callback')

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
    
    # Переходим к запросу геолокации
    context.user_data['registration_step'] = 'location'
    
    keyboard = [
        [InlineKeyboardButton("📍 Отправить геолокацию", callback_data="send_location")],
        [InlineKeyboardButton("🌍 Выбрать часовой пояс вручную", callback_data="manual_timezone")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🌍 **Определение часового пояса**\n\n"
        "Для автоматического определения вашего часового пояса отправьте геолокацию.\n\n"
        "Это необходимо для корректной отправки напоминаний о приемах пищи.\n\n"
        "**Выберите способ:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

__all__.append('handle_goal_callback')

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /reset"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if not existing_user:
            await bf.send_not_registered_message(update, context)
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

__all__.append('reset_command')

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
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "ℹ️ **Нет данных для удаления**\n\n"
                "У вас нет записей о приемах пищи за сегодняшний день.",
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in dayreset command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при удалении данных. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )

__all__.append('dayreset_command')

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
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Произошла ошибка при сбросе счетчиков. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard_for_user(update)
            )
            
    except Exception as e:
        logger.error(f"Error in resetcounters command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при сбросе счетчиков. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )

__all__.append('resetcounters_command')

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /add"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if not existing_user:
            await bf.send_not_registered_message(update, context)
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

__all__.append('add_command')

async def addvoice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /addvoice"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if not existing_user:
            await bf.send_not_registered_message(update, context)
            return
    except Exception as e:
        logger.error(f"Error in addvoice_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при проверке регистрации. Попробуйте позже."
        )
        return
    
    # Устанавливаем состояние ожидания голосового сообщения для проверки калорий
    context.user_data['waiting_for_check_voice'] = True
    
    await update.message.reply_text(
        "🎤 **Анализ голосового описания блюда**\n\n"
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
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('addvoice_command')

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов"""
    query = update.callback_query
    user = update.effective_user
    
    # Логируем только в режиме разработки
    if TEST_MODE:
        logger.debug(f"handle_callback_query: user={user.id}, data={query.data}")
    
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
        # Продолжаем обработку даже если не удалось ответить на callback
    
    # Добавляем информацию о callback
    logger.info(f"Callback query received from user {user.id}: {query.data}")
    
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
        await bf.help_command(update, context)
    elif query.data == "main_menu":
        # Просто показываем главное меню в новом сообщении
        await query.message.reply_text(
            "🏠 **Главное меню**\n\n"
            "Выберите нужную функцию:",
            reply_markup=get_main_menu_keyboard_for_user(update),
            parse_mode='Markdown'
        )
    elif query.data == "subscription":
        await bf.show_subscription_purchase_menu(update, context)
    elif query.data == "buy_subscription":
        await bf.show_subscription_purchase_menu(update, context)
    elif query.data == "terms":
        await bf.terms_command(update, context)
    elif query.data.startswith('gender_'):
        await bf.handle_gender_callback(update, context)
    elif query.data.startswith('activity_'):
        await bf.handle_activity_callback(update, context)
    elif query.data.startswith('goal_'):
        await bf.handle_goal_callback(update, context)
    elif query.data == "send_location":
        await handle_send_location_callback(update, context)
    elif query.data == "manual_timezone":
        await handle_manual_timezone_callback(update, context)
    elif query.data.startswith('tz_') or query.data == 'tz_other' or query.data.startswith('tz_group_') or query.data.startswith('tz_hemisphere_') or query.data == 'tz_back_to_hemispheres':
        await bf.handle_timezone_callback(update, context)
    elif query.data == "reset_confirm":
        await bf.handle_reset_confirm(update, context)
    elif query.data == "add_dish":
        await bf.handle_add_dish(update, context)
    elif query.data == "check_calories":
        await bf.handle_check_calories(update, context)
    elif query.data == "addmeal":
        await bf.handle_addmeal_callback(update, context)
    elif query.data == "menu_from_meal_selection":
        await bf.handle_menu_from_meal_selection(update, context)
    elif query.data == "profile":
        await bf.handle_profile_callback(update, context)
    elif query.data == "back_to_main":
        await bf.handle_back_to_main(update, context)
    elif query.data.startswith('meal_'):
        await bf.handle_meal_selection(update, context)
    elif query.data == "analyze_photo":
        await bf.handle_analyze_photo_callback(update, context)
    elif query.data == "analyze_text":
        await bf.handle_analyze_text_callback(update, context)
    elif query.data == "analyze_voice":
        await bf.handle_analyze_voice_callback(update, context)
    elif query.data == "analyze_photo_text":
        await bf.handle_analyze_photo_text_callback(update, context)
    elif query.data == "check_photo":
        await bf.handle_check_photo_callback(update, context)
    elif query.data == "check_text":
        await bf.handle_check_text_callback(update, context)
    elif query.data == "check_voice":
        await bf.handle_check_voice_callback(update, context)
    elif query.data == "check_photo_text":
        await bf.handle_check_photo_text_callback(update, context)
    elif query.data == "statistics":
        await bf.handle_statistics_callback(update, context)
    elif query.data == "stats_today":
        await bf.handle_stats_today_callback(update, context)
    elif query.data == "stats_yesterday":
        await bf.handle_stats_yesterday_callback(update, context)
    elif query.data == "stats_week":
        await bf.handle_stats_week_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_stats']:
        await bf.handle_admin_stats_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_users']:
        await bf.handle_admin_users_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_meals']:
        await bf.handle_admin_meals_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_broadcast']:
        await bf.handle_admin_broadcast_callback(update, context)
    elif query.data == "broadcast_create":
        await bf.handle_broadcast_create_callback(update, context)
    elif query.data == "broadcast_stats":
        await bf.handle_broadcast_stats_callback(update, context)
    elif query.data == "broadcast_confirm":
        await bf.handle_broadcast_confirm_callback(update, context)
    elif query.data == "broadcast_cancel":
        await bf.handle_broadcast_cancel_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_subscriptions']:
        await bf.handle_admin_subscriptions_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_check_subscription']:
        await bf.handle_admin_check_subscription_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_manage_subscription']:
        await bf.handle_admin_manage_subscription_callback(update, context)
    elif query.data.startswith(ADMIN_CALLBACKS['admin_activate_trial'] + ':'):
        await bf.handle_admin_activate_trial_callback(update, context)
    elif query.data.startswith(ADMIN_CALLBACKS['admin_activate_premium'] + ':'):
        await bf.handle_admin_activate_premium_callback(update, context)
    elif query.data.startswith(ADMIN_CALLBACKS['admin_deactivate_subscription'] + ':'):
        await bf.handle_admin_deactivate_subscription_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_back']:
        await bf.handle_admin_back_callback(update, context)
    elif query.data == ADMIN_CALLBACKS['admin_panel']:
        await bf.show_admin_panel(update, context)
    elif query.data == "buy_subscription":
        await bf.show_subscription_purchase_menu(update, context)
    elif query.data.startswith("buy_"):
        await bf.handle_subscription_purchase(update, context)
    elif query.data == "separator":
        # Игнорируем нажатие на разделитель
        await query.answer()
    elif query.data == "admin_star_balance":
        await bf.handle_admin_star_balance_callback(update, context)
    elif query.data == "cancel_analysis":
        await bf.handle_cancel_analysis(update, context)
    elif query.data == "confirm_analysis":
        await bf.handle_confirm_analysis(update, context)
    elif query.data == "add_to_analysis":
        await bf.handle_add_to_analysis(update, context)
    elif query.data == "confirm_check_analysis":
        await bf.handle_confirm_check_analysis(update, context)
    elif query.data == "add_to_check_analysis":
        await bf.handle_add_to_check_analysis(update, context)
    elif query.data == "confirm_photo_text_analysis":
        await bf.handle_confirm_photo_text_analysis(update, context)
    elif query.data == "add_to_photo_text_analysis":
        await bf.handle_add_to_photo_text_analysis(update, context)
    elif query.data == "confirm_photo_text_check_analysis":
        await bf.handle_confirm_photo_text_check_analysis(update, context)
    elif query.data == "add_to_photo_text_check_analysis":
        await bf.handle_add_to_photo_text_check_analysis(update, context)
    elif query.data == "confirm_text_analysis":
        await bf.handle_confirm_text_analysis(update, context)
    elif query.data == "add_to_text_analysis":
        await bf.handle_add_to_text_analysis(update, context)
    elif query.data == "confirm_check_text_analysis":
        await bf.handle_confirm_check_text_analysis(update, context)
    elif query.data == "add_to_check_text_analysis":
        await bf.handle_add_to_check_text_analysis(update, context)
    elif query.data == "cancel_text_analysis":
        await bf.handle_cancel_text_analysis(update, context)
    else:
        # Если callback data не распознан
        logger.warning(f"Unknown callback data: {query.data}")
        await query.message.reply_text(
            "❌ Неизвестная команда. Попробуйте снова.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )

__all__.append('handle_callback_query')

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

__all__.append('handle_gender_callback')

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

__all__.append('handle_reset_confirm')

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
            reply_markup=get_main_menu_keyboard_for_user(update),
            parse_mode='Markdown'
        )
        return
    
    # Сбрасываем флаги дополнений для нового анализа
    context.user_data.pop('photo_text_additional_used', None)
    context.user_data.pop('photo_text_check_additional_used', None)
    context.user_data.pop('text_additional_used', None)
    context.user_data.pop('check_text_additional_used', None)
    
    # Создаем подменю для выбора приема пищи
    # Теперь пользователь может добавлять несколько блюд для каждого приема пищи
    keyboard = [
        [InlineKeyboardButton("🌅 Завтрак", callback_data="meal_breakfast")],
        [InlineKeyboardButton("☀️ Обед", callback_data="meal_lunch")],
        [InlineKeyboardButton("🌙 Ужин", callback_data="meal_dinner")],
        [InlineKeyboardButton("🍎 Перекус", callback_data="meal_snack")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Формируем сообщение
    message_text = "🍽️ **Добавить блюдо**\n\n"
    message_text += "Выберите прием пищи:"
    
    await query.edit_message_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

__all__.append('handle_add_dish')



async def handle_cancel_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Отмена' для отмены анализа"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем все состояния ожидания
    context.user_data.pop('waiting_for_photo', None)
    context.user_data.pop('waiting_for_text', None)
    context.user_data.pop('waiting_for_voice', None)
    context.user_data.pop('waiting_for_photo_text', None)
    context.user_data.pop('waiting_for_photo_text_additional', None)
    context.user_data.pop('waiting_for_photo_text_check_additional', None)
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
    
    # Очищаем флаги дополнения анализа
    context.user_data.pop('analysis_supplemented', None)
    context.user_data.pop('check_analysis_supplemented', None)
    context.user_data.pop('waiting_for_additional_text', None)
    context.user_data.pop('waiting_for_check_additional_text', None)
    context.user_data.pop('waiting_for_photo_confirmation', None)
    context.user_data.pop('original_analysis', None)
    context.user_data.pop('original_calories', None)
    context.user_data.pop('original_dish_name', None)
    context.user_data.pop('calories_display', None)
    
    # Показываем главное меню
    await query.edit_message_text(
        "🏠 **Главное меню**\n\n"
        "Выберите нужную функцию:",
        reply_markup=get_main_menu_keyboard_for_user(update),
        parse_mode='Markdown'
    )

__all__.append('handle_cancel_analysis')

async def handle_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Назад в меню'"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🏠 **Главное меню**\n\n"
        "Выберите нужную функцию:",
        reply_markup=get_main_menu_keyboard_for_user(update),
        parse_mode='Markdown'
    )

__all__.append('handle_back_to_main')

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

__all__.append('handle_pre_checkout_query')



async def handle_universal_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик универсального анализа
    Определяет тип данных и вызывает соответствующую функцию
    """
    user = update.effective_user
    message = update.message
    
    logger.info(f"Universal analysis from user {user.id}")
    
    # Сбрасываем флаги дополнений для нового анализа (только если это не дополнение)
    if not context.user_data.get('waiting_for_additional_text', False) and not context.user_data.get('waiting_for_check_additional_text', False):
        context.user_data.pop('photo_text_additional_used', None)
        context.user_data.pop('photo_text_check_additional_used', None)
        context.user_data.pop('text_additional_used', None)
        context.user_data.pop('check_text_additional_used', None)
    
    # Проверяем, не ожидается ли ввод Telegram ID для админки
    if context.user_data.get('admin_waiting_for_telegram_id', False):
        logger.info(f"Admin waiting for telegram ID, redirecting to handle_text_input for user {user.id}")
        # Если ожидается ввод для админки, передаем управление handle_text_input
        await bf.handle_text_input(update, context)
        return
    
    # Проверяем, не ожидается ли ввод текста для рассылки
    if context.user_data.get('waiting_for_broadcast_text', False):
        # Если ожидается ввод текста для рассылки, передаем управление handle_broadcast_text_input
        await bf.handle_broadcast_text_input(update, context)
        return
    
    # Проверяем, не идет ли процесс регистрации
    if 'registration_step' in context.user_data:
        # Если идет регистрация, передаем управление handle_text_input
        await bf.handle_text_input(update, context)
        return
    
    # Проверяем, ожидается ли дополнительный текст для дополнения анализа
    waiting_for_additional = context.user_data.get('waiting_for_additional_text', False)
    waiting_for_check_additional = context.user_data.get('waiting_for_check_additional_text', False)
    
    if waiting_for_additional:
        logger.info(f"Handling additional text analysis for user {user.id}")
        await bf.handle_additional_text_analysis(update, context)
        return
    elif waiting_for_check_additional:
        logger.info(f"Handling check additional text analysis for user {user.id}")
        await bf.handle_check_additional_text_analysis(update, context)
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
    
    # Проверяем, ожидается ли дополнительный текст для фото + текст
    if context.user_data.get('waiting_for_photo_text_additional'):
        await bf.handle_photo_text_additional_analysis(update, context)
        return
    elif context.user_data.get('waiting_for_photo_text_check_additional'):
        await bf.handle_photo_text_check_additional_analysis(update, context)
        return
    
    # Определяем тип данных
    if message.photo:
        # Проверяем, есть ли текст вместе с фото
        if message.caption and message.caption.strip():
            # Фото + текст - уточненный анализ
            logger.info(f"Photo with text analysis for user {user.id}: '{message.caption[:50]}...'")
            if context.user_data.get('save_mode'):
                # Режим сохранения
                context.user_data['waiting_for_photo_text'] = True
            else:
                # Режим проверки калорий для команды /analyze
                context.user_data['check_mode'] = True
                context.user_data['waiting_for_check_photo_text'] = True
            await bf.handle_photo_with_text(update, context)
        else:
            # Только фото
            logger.info(f"Photo analysis for user {user.id}")
            if context.user_data.get('save_mode'):
                # Режим сохранения
                context.user_data['waiting_for_photo'] = True
            else:
                # Режим проверки калорий для команды /analyze
                context.user_data['check_mode'] = True
                context.user_data['waiting_for_check_photo'] = True
            await bf.handle_photo(update, context)
        
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
        await bf.handle_voice(update, context)
        
    elif message.text and not message.text.startswith('/'):
        # Текстовое описание
        logger.info(f"Text analysis for user {update.effective_user.id}")
        if context.user_data.get('save_mode'):
            # Режим сохранения - устанавливаем флаг для автоматического сохранения
            context.user_data['auto_save'] = True
        else:
            # Режим проверки калорий для команды /analyze
            context.user_data['check_mode'] = True
        # Вызываем функцию анализа текста напрямую
        await bf.handle_food_text_analysis(update, context)
        
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

__all__.append('handle_universal_analysis')

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
                reply_markup=get_main_menu_keyboard_for_user(update)
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
                    reply_markup=get_main_menu_keyboard_for_user(update),
                    parse_mode='Markdown'
                )
                return
        
        # Устанавливаем режим проверки калорий для универсального анализа
        context.user_data['check_mode'] = True
        
        # Сбрасываем флаги дополнений для нового анализа
        context.user_data.pop('photo_text_additional_used', None)
        context.user_data.pop('photo_text_check_additional_used', None)
        context.user_data.pop('text_additional_used', None)
        context.user_data.pop('check_text_additional_used', None)
        
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
            reply_markup=get_main_menu_keyboard_for_user(update)
        )

__all__.append('handle_check_calories')

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
            
            # Парсим результат анализа для извлечения БЖУ
            calories, protein, fat, carbs = extract_macros_from_analysis(analysis_result)
            
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
                    meal_name = context.user_data.get('meal_name_name', 'Прием пищи')
                    meal_info = f"**🍽️ {meal_name}**\n\n{combined_analysis}"
                    
                    # Сохраняем в базу данных
                    try:
                        meal_type = context.user_data.get('meal_name', 'meal_breakfast')
                        
                        success = add_meal(
                            telegram_id=user.id,
                            meal_type=meal_type,
                            meal_name=meal_info,
                            dish_name=dish_name,
                            calories=calories,
                            protein=protein,
                            fat=fat,
                            carbs=carbs,
                            analysis_type="text"
                        )
                        
                        if success:
                            await processing_msg.edit_text(
                                f"✅ **Блюдо добавлено в {meal_name}!**\n\n"
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
                # Режим проверки калорий - показываем результат с кнопками подтверждения
                # Сохраняем данные анализа для подтверждения
                context.user_data['original_analysis'] = analysis_result
                context.user_data['original_calories'] = calories
                context.user_data['original_dish_name'] = dish_name
                context.user_data['waiting_for_text_confirmation'] = True
                context.user_data['check_mode'] = True
                
                cleaned_result = clean_markdown_text(analysis_result)
                result_text = f"🔍 **Анализ калорий**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ будут сохранены в статистику**"
                
                await processing_msg.edit_text(
                    result_text, 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_check_text_analysis")],
                        [InlineKeyboardButton("✏️ Дополнить", callback_data="add_to_check_text_analysis")],
                        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_text_analysis")]
                    ]), 
                    parse_mode='Markdown'
                )
            else:
                # Режим добавления блюда - показываем результат с кнопками подтверждения
                # Сохраняем данные анализа для подтверждения
                context.user_data['original_analysis'] = analysis_result
                context.user_data['original_calories'] = calories
                context.user_data['original_dish_name'] = dish_name
                context.user_data['waiting_for_text_confirmation'] = True
                context.user_data['save_mode'] = True
                
                meal_name = context.user_data.get('meal_name_name', 'Прием пищи')
                meal_info = f"**🍽️ {meal_name}**\n\n{analysis_result}"
                cleaned_meal_info = clean_markdown_text(meal_info)
                
                await processing_msg.edit_text(
                    cleaned_meal_info, 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_text_analysis")],
                        [InlineKeyboardButton("✏️ Дополнить", callback_data="add_to_text_analysis")],
                        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_text_analysis")]
                    ]), 
                    parse_mode='Markdown'
                )
                return
                
                # Старый код для автоматического сохранения (закомментирован)
                # try:
                #     meal_type = context.user_data.get('meal_name', 'meal_breakfast')
                #     meal_name = context.user_data.get('meal_name_name', 'Прием пищи')
                #     
                #     # Сохраняем в базу данных
                #     success = add_meal(
                #         telegram_id=user.id,
                #         meal_type=meal_type,
                #         meal_name=meal_name,
                #         dish_name=dish_name,
                #         calories=calories,
                #         analysis_type="text"
                #     )
                #     
                #     if success:
                #         logger.info(f"Meal saved successfully for user {user.id}")
                #         cleaned_result = clean_markdown_text(analysis_result)
                #         await processing_msg.edit_text(cleaned_result, reply_markup=get_analysis_result_keyboard(), parse_mode='Markdown')
                #     else:
                #         logger.warning(f"Failed to save meal for user {user.id}")
                #         await processing_msg.edit_text(
                #             "❌ Ошибка сохранения\n\n"
                #             "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                #             reply_markup=get_main_menu_keyboard_for_user(update)
                #         )
                #     
                # except Exception as e:
                #     logger.error(f"Error saving meal to database: {e}")
                #     await processing_msg.edit_text(
                #         "❌ Ошибка сохранения\n\n"
                #         "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                #         reply_markup=get_main_menu_keyboard()
                #     )
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
                reply_markup=get_main_menu_keyboard_for_user(update),
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
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing text description: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка\n\n"
            "Не удалось обработать описание блюда. Попробуйте позже или используйте команду /addtext снова.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )
    finally:
        # Очищаем флаги режимов
        context.user_data.pop('auto_save', None)
        context.user_data.pop('save_mode', None)

__all__.append('handle_food_text_analysis')

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
    context.user_data['meal_name'] = query.data
    context.user_data['meal_name_name'] = meal_name
    
    # Устанавливаем режим сохранения для автоматического анализа
    context.user_data['save_mode'] = True
    
    # Сбрасываем флаги дополнений для нового анализа
    context.user_data.pop('photo_text_additional_used', None)
    context.user_data.pop('photo_text_check_additional_used', None)
    context.user_data.pop('text_additional_used', None)
    context.user_data.pop('check_text_additional_used', None)
    
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

__all__.append('handle_meal_selection')

async def handle_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Профиль' - вызывает команду /profile"""
    query = update.callback_query
    await query.answer()
    
    # Получаем информацию о пользователе
    user = update.effective_user
    if TEST_MODE:
        logger.debug(f"handle_profile_callback called by user {user.id}")
    
    # Создаем фиктивный update для команды /profile
    from handlers.profile import profile_command
    
    # Создаем объект message из callback query
    class MockMessage:
        def __init__(self, callback_query):
            self.from_user = callback_query.from_user
            self.chat = callback_query.message.chat
            self.message_id = callback_query.message.message_id
            self.reply_text = callback_query.edit_message_text
            self.text = "/profile"
    
    # Создаем фиктивный update
    class MockUpdate:
        def __init__(self, callback_query):
            self.effective_user = callback_query.from_user
            self.message = MockMessage(callback_query)
            self.callback_query = callback_query
    
    mock_update = MockUpdate(query)
    
    try:
        # Вызываем команду /profile
        await profile_command(mock_update, context)
    except Exception as e:
        logger.error(f"Error in handle_profile_callback: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при загрузке профиля. Попробуйте позже."
        )

__all__.append('handle_profile_callback')

async def handle_stats_today_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Статистика за сегодня'"""
    query = update.callback_query
    await query.answer()
    
    # Вызываем функцию статистики
    from handlers.profile import show_meal_statistics
    await show_meal_statistics(update, context)

__all__.append('handle_stats_today_callback')

async def handle_statistics_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Статистика' - показывает меню статистики"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем подписку
    access_info = check_subscription_access(user.id)
    if not access_info['has_access']:
        from handlers.subscription import get_subscription_message
        subscription_msg = get_subscription_message(access_info)
        await query.edit_message_text(
            subscription_msg,
            reply_markup=get_main_menu_keyboard_for_user(update),
            parse_mode='Markdown'
        )
        return
    
    # Создаем меню статистики
    stats_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 За сегодня", callback_data="stats_today")],
        [InlineKeyboardButton("📈 За вчера", callback_data="stats_yesterday")],
        [InlineKeyboardButton("📅 За неделю", callback_data="stats_week")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ])
    
    await query.edit_message_text(
        "📊 **Статистика**\n\n"
        "Выберите период для просмотра статистики:",
        reply_markup=stats_keyboard,
        parse_mode='Markdown'
    )

__all__.append('handle_statistics_callback')

async def handle_stats_yesterday_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Статистика за вчера'"""
    query = update.callback_query
    await query.answer()
    
    # Пока что перенаправляем на статистику за сегодня
    # TODO: Реализовать статистику за вчера
    from handlers.profile import show_meal_statistics
    await show_meal_statistics(update, context)

__all__.append('handle_stats_yesterday_callback')

async def handle_stats_week_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Статистика за неделю'"""
    query = update.callback_query
    await query.answer()
    
    # Пока что перенаправляем на статистику за сегодня
    # TODO: Реализовать статистику за неделю
    from handlers.profile import show_meal_statistics
    await show_meal_statistics(update, context)

__all__.append('handle_stats_week_callback')

async def handle_confirm_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Все верно?' для режима добавления блюда"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Получаем сохраненные данные анализа
    original_analysis = context.user_data.get('original_analysis', '')
    original_calories = context.user_data.get('original_calories', 0)
    original_dish_name = context.user_data.get('original_dish_name', 'Блюдо по фото')
    
    if not original_analysis:
        await query.edit_message_text(
            "❌ Ошибка: данные анализа не найдены. Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )
        return
    
    # Очищаем состояния
    context.user_data.pop('waiting_for_photo_confirmation', None)
    context.user_data.pop('original_analysis', None)
    context.user_data.pop('original_calories', None)
    context.user_data.pop('original_dish_name', None)
    context.user_data.pop('save_mode', None)
    context.user_data.pop('analysis_supplemented', None)
    context.user_data.pop('calories_display', None)
    
    # Сохраняем в базу данных
    try:
        meal_name = context.user_data.get('meal_name_name', 'Прием пищи')
        meal_type = context.user_data.get('meal_name', 'meal_breakfast')
        
        logger.info(f"Confirming analysis for user {user.id}: meal_type={meal_type}, meal_name={meal_name}, dish_name={original_dish_name}, calories={original_calories}")
        
        # Извлекаем БЖУ из анализа
        from services.food_analysis_service import extract_macros_from_analysis
        calories_from_analysis, protein, fat, carbs = extract_macros_from_analysis(original_analysis)
        
        success = add_meal(
            telegram_id=user.id,
            meal_type=meal_type,
            meal_name=meal_name,
            dish_name=original_dish_name,
            calories=original_calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
            analysis_type="photo"
        )
        
        if success:
            logger.info(f"Meal saved successfully for user {user.id}")
            meal_info = f"**🍽️ {meal_name}**\n\n{original_analysis}"
            cleaned_meal_info = clean_markdown_text(meal_info)
            
            await query.edit_message_text(
                f"✅ **Блюдо добавлено в статистику!**\n\n{cleaned_meal_info}",
                reply_markup=get_analysis_result_keyboard(),
                parse_mode='Markdown'
            )
        else:
            logger.warning(f"Failed to save meal for user {user.id}")
            await query.edit_message_text(
                "❌ Ошибка сохранения\n\n"
                "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                reply_markup=get_main_menu_keyboard_for_user(update)
            )
            
    except Exception as e:
        logger.error(f"Error saving meal to database: {e}")
        await query.edit_message_text(
            "❌ Ошибка сохранения\n\n"
            "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )

__all__.append('handle_confirm_analysis')

async def handle_add_to_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Дополнить' для режима добавления блюда"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, не использовал ли пользователь уже возможность дополнения
    if context.user_data.get('analysis_supplemented', False):
        await query.edit_message_text(
            "❌ Вы уже использовали возможность дополнения анализа.\n\n"
            "Можно дополнить анализ только один раз.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_analysis")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
            ])
        )
        return
    
    # Устанавливаем состояние ожидания дополнительного текста
    context.user_data['waiting_for_additional_text'] = True
    context.user_data['analysis_supplemented'] = True
    
    logger.info(f"Set waiting_for_additional_text=True for user {query.from_user.id}")
    
    await query.edit_message_text(
        "✏️ **Дополнение анализа**\n\n"
        "Отправьте текстовое описание с уточнениями:\n"
        "• Размер порции (\"большая тарелка\", \"2 куска\", \"примерно 300г\")\n"
        "• Дополнительные ингредиенты (\"с добавлением сыра\", \"без масла\")\n"
        "• Способ приготовления (\"домашний рецепт\", \"жареное\")\n\n"
        "**Примеры уточнений:**\n"
        "• \"Большая порция, диаметр 30см, с добавлением моцареллы\"\n"
        "• \"2 куска, домашний рецепт, без масла\"\n"
        "• \"Примерно 250г, с двойной порцией мяса\"\n\n"
        "⚠️ **Можно дополнить анализ только один раз!**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_add_to_analysis')

async def handle_confirm_check_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Все верно?' для режима проверки калорий"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Получаем сохраненные данные анализа
    original_analysis = context.user_data.get('original_analysis', '')
    original_calories = context.user_data.get('original_calories', 0)
    original_dish_name = context.user_data.get('original_dish_name', 'Блюдо по фото')
    
    if not original_analysis:
        await query.edit_message_text(
            "❌ Ошибка: данные анализа не найдены. Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )
        return
    
    # Очищаем состояния
    context.user_data.pop('waiting_for_photo_confirmation', None)
    context.user_data.pop('original_analysis', None)
    context.user_data.pop('original_calories', None)
    context.user_data.pop('original_dish_name', None)
    context.user_data.pop('check_mode', None)
    context.user_data.pop('check_analysis_supplemented', None)
    context.user_data.pop('calories_display', None)
    
    # Записываем использование функции
    add_calorie_check(user.id, 'photo')
    
    # Показываем финальный результат
    cleaned_result = clean_markdown_text(original_analysis)
    result_text = f"🔍 **Анализ калорий**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ сохранены в статистику**"
    
    await query.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_confirm_check_analysis')

async def handle_confirm_check_text_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Все верно?' для режима проверки калорий (текст)"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Получаем сохраненные данные анализа
    original_analysis = context.user_data.get('original_analysis', '')
    original_calories = context.user_data.get('original_calories', 0)
    original_dish_name = context.user_data.get('original_dish_name', 'Блюдо по описанию')
    
    if not original_analysis:
        await query.edit_message_text(
            "❌ Ошибка: данные анализа не найдены. Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )
        return
    
    # Очищаем состояния
    context.user_data.pop('waiting_for_text_confirmation', None)
    context.user_data.pop('original_analysis', None)
    context.user_data.pop('original_calories', None)
    context.user_data.pop('original_dish_name', None)
    context.user_data.pop('check_mode', None)
    context.user_data.pop('check_analysis_supplemented', None)
    context.user_data.pop('calories_display', None)
    
    # Записываем использование функции
    add_calorie_check(user.id, 'text')
    
    # Показываем финальный результат
    cleaned_result = clean_markdown_text(original_analysis)
    result_text = f"🔍 **Анализ калорий**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ сохранены в статистику**"
    
    await query.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_confirm_check_text_analysis')

async def handle_confirm_text_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Все верно?' для режима добавления блюда (текст)"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Получаем сохраненные данные анализа
    original_analysis = context.user_data.get('original_analysis', '')
    original_calories = context.user_data.get('original_calories', 0)
    original_dish_name = context.user_data.get('original_dish_name', 'Блюдо по описанию')
    
    if not original_analysis:
        await query.edit_message_text(
            "❌ Ошибка: данные анализа не найдены. Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )
        return
    
    # Очищаем состояния
    context.user_data.pop('waiting_for_text_confirmation', None)
    context.user_data.pop('original_analysis', None)
    context.user_data.pop('original_calories', None)
    context.user_data.pop('original_dish_name', None)
    context.user_data.pop('save_mode', None)
    context.user_data.pop('calories_display', None)
    
    # Сохраняем в базу данных
    try:
        meal_name = context.user_data.get('meal_name_name', 'Прием пищи')
        meal_type = context.user_data.get('meal_name', 'meal_breakfast')
        
        logger.info(f"Confirming text analysis for user {user.id}: meal_type={meal_type}, meal_name={meal_name}, dish_name={original_dish_name}, calories={original_calories}")
        
        # Извлекаем БЖУ из анализа
        from services.food_analysis_service import extract_macros_from_analysis
        calories_from_analysis, protein, fat, carbs = extract_macros_from_analysis(original_analysis)
        
        success = add_meal(
            telegram_id=user.id,
            meal_type=meal_type,
            meal_name=meal_name,
            dish_name=original_dish_name,
            calories=original_calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
            analysis_type="text"
        )
        
        if success:
            logger.info(f"Meal saved successfully for user {user.id}")
            meal_info = f"**🍽️ {meal_name}**\n\n{original_analysis}"
            cleaned_meal_info = clean_markdown_text(meal_info)
            
            await query.edit_message_text(
                f"✅ **Блюдо добавлено в статистику!**\n\n{cleaned_meal_info}",
                reply_markup=get_analysis_result_keyboard(),
                parse_mode='Markdown'
            )
        else:
            logger.warning(f"Failed to save meal for user {user.id}")
            await query.edit_message_text(
                "❌ Ошибка сохранения\n\n"
                "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                reply_markup=get_main_menu_keyboard_for_user(update)
            )
            
    except Exception as e:
        logger.error(f"Error saving meal to database: {e}")
        await query.edit_message_text(
            "❌ Ошибка сохранения\n\n"
            "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )

__all__.append('handle_confirm_text_analysis')

async def handle_add_to_text_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Дополнить' для режима добавления блюда (текст)"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, не использовал ли пользователь уже возможность дополнения
    if context.user_data.get('text_analysis_supplemented', False):
        await query.edit_message_text(
            "❌ Вы уже использовали возможность дополнения анализа.\n\n"
            "Можно дополнить анализ только один раз.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_text_analysis")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_text_analysis")]
            ])
        )
        return
    
    # Устанавливаем состояние ожидания дополнительного текста
    context.user_data['waiting_for_additional_text'] = True
    context.user_data['text_analysis_supplemented'] = True
    
    logger.info(f"Set waiting_for_additional_text=True for user {query.from_user.id}")
    
    await query.edit_message_text(
        "✏️ **Дополнение анализа**\n\n"
        "Отправьте текстовое описание с уточнениями:\n"
        "• Размер порции (\"большая тарелка\", \"2 куска\", \"примерно 300г\")\n"
        "• Дополнительные ингредиенты (\"с добавлением сыра\", \"без масла\")\n"
        "• Способ приготовления (\"домашний рецепт\", \"жареное\")\n\n"
        "**Примеры уточнений:**\n"
        "• \"Большая порция, диаметр 30см, с добавлением моцареллы\"\n"
        "• \"2 куска, домашний рецепт, без масла\"\n"
        "• \"Примерно 250г, с двойной порцией мяса\"\n\n"
        "⚠️ **Можно дополнить анализ только один раз!**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_text_analysis")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_add_to_text_analysis')

async def handle_add_to_check_text_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Дополнить' для режима проверки калорий (текст)"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, не использовал ли пользователь уже возможность дополнения
    if context.user_data.get('check_text_analysis_supplemented', False):
        await query.edit_message_text(
            "❌ Вы уже использовали возможность дополнения анализа.\n\n"
            "Можно дополнить анализ только один раз.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_check_text_analysis")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_text_analysis")]
            ])
        )
        return
    
    # Устанавливаем состояние ожидания дополнительного текста
    context.user_data['waiting_for_check_additional_text'] = True
    context.user_data['check_text_analysis_supplemented'] = True
    
    logger.info(f"Set waiting_for_check_additional_text=True for user {query.from_user.id}")
    
    await query.edit_message_text(
        "✏️ **Дополнение анализа**\n\n"
        "Отправьте текстовое описание с уточнениями:\n"
        "• Размер порции (\"большая тарелка\", \"2 куска\", \"примерно 300г\")\n"
        "• Дополнительные ингредиенты (\"с добавлением сыра\", \"без масла\")\n"
        "• Способ приготовления (\"домашний рецепт\", \"жареное\")\n\n"
        "**Примеры уточнений:**\n"
        "• \"Большая порция, диаметр 30см, с добавлением моцареллы\"\n"
        "• \"2 куска, домашний рецепт, без масла\"\n"
        "• \"Примерно 250г, с двойной порцией мяса\"\n\n"
        "⚠️ **Можно дополнить анализ только один раз!**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_text_analysis")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_add_to_check_text_analysis')

async def handle_cancel_text_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Отменить' для текстового анализа"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем все состояния
    context.user_data.pop('waiting_for_text_confirmation', None)
    context.user_data.pop('original_analysis', None)
    context.user_data.pop('original_calories', None)
    context.user_data.pop('original_dish_name', None)
    context.user_data.pop('save_mode', None)
    context.user_data.pop('check_mode', None)
    context.user_data.pop('text_analysis_supplemented', None)
    context.user_data.pop('check_text_analysis_supplemented', None)
    context.user_data.pop('calories_display', None)
    
    await query.edit_message_text(
        "❌ **Анализ отменен**\n\n"
        "Вы можете попробовать снова, отправив новое описание блюда.",
        reply_markup=get_main_menu_keyboard_for_user(update),
        parse_mode='Markdown'
    )

__all__.append('handle_cancel_text_analysis')

async def handle_add_to_check_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Дополнить' для режима проверки калорий"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, не использовал ли пользователь уже возможность дополнения
    if context.user_data.get('check_analysis_supplemented', False):
        await query.edit_message_text(
            "❌ Вы уже использовали возможность дополнения анализа.\n\n"
            "Можно дополнить анализ только один раз.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_check_analysis")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
            ])
        )
        return
    
    # Устанавливаем состояние ожидания дополнительного текста
    context.user_data['waiting_for_check_additional_text'] = True
    context.user_data['check_analysis_supplemented'] = True
    
    logger.info(f"Set waiting_for_check_additional_text=True for user {query.from_user.id}")
    
    await query.edit_message_text(
        "✏️ **Дополнение анализа**\n\n"
        "Отправьте текстовое описание с уточнениями:\n"
        "• Размер порции (\"большая тарелка\", \"2 куска\", \"примерно 300г\")\n"
        "• Дополнительные ингредиенты (\"с добавлением сыра\", \"без масла\")\n"
        "• Способ приготовления (\"домашний рецепт\", \"жареное\")\n\n"
        "**Примеры уточнений:**\n"
        "• \"Большая порция, диаметр 30см, с добавлением моцареллы\"\n"
        "• \"2 куска, домашний рецепт, без масла\"\n"
        "• \"Примерно 250г, с двойной порцией мяса\"\n\n"
        "⚠️ **Можно дополнить анализ только один раз!**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_add_to_check_analysis')

async def handle_additional_text_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик дополнительного текста для дополнения анализа фото (режим добавления)"""
    user = update.effective_user
    message = update.message
    additional_text = message.text.strip() if message.text else ""
    
    if not additional_text:
        await message.reply_text(
            "❌ Ошибка: пустое описание. Пожалуйста, отправьте текстовое описание с уточнениями.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
            ])
        )
        return
    
    # Получаем оригинальный анализ
    original_analysis = context.user_data.get('original_analysis', '')
    original_calories = context.user_data.get('original_calories', 0)
    original_dish_name = context.user_data.get('original_dish_name', 'Блюдо по фото')
    
    logger.info(f"Original analysis length: {len(original_analysis) if original_analysis else 0}")
    logger.info(f"Additional text: '{additional_text}'")
    
    if not original_analysis or not original_analysis.strip():
        logger.error(f"Original analysis is empty or None: '{original_analysis}'")
        await message.reply_text(
            "❌ Ошибка: данные анализа не найдены. Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )
        return
    
    # Отправляем сообщение о начале обработки
    processing_msg = await message.reply_text(
        "🔄 **Обрабатываю дополнение...**\n\n"
        "Анализирую уточнения с помощью ИИ модели...",
        parse_mode='Markdown'
    )
    
    try:
        # Создаем комбинированный запрос
        combined_prompt = f"Исходный анализ фото:\n{original_analysis}\n\nДополнительная информация от пользователя:\n{additional_text}\n\nНа основе исходного анализа и дополнительной информации, предоставь уточненный расчет калорий и БЖУ."
        
        logger.info(f"Combined prompt length: {len(combined_prompt)}")
        logger.info(f"Combined prompt preview: {combined_prompt[:200]}...")
        
        # Анализируем дополнительный текст с помощью специальной функции
        additional_analysis = await analyze_food_supplement(combined_prompt)
        
        if additional_analysis and is_valid_analysis(additional_analysis):
            # Объединяем оригинальный анализ с дополнительным
            combined_analysis = f"{original_analysis}\n\n**📝 Дополнения:**\n{additional_text}\n\n**🔄 Уточненный расчет:**\n{additional_analysis}"
            
            # Извлекаем новые калории из дополненного анализа
            new_calories = extract_calories_from_analysis(additional_analysis)
            if new_calories and new_calories > 0:
                # Используем новые калории
                final_calories = new_calories
                calories_display = f"{original_calories} → {new_calories} ккал"
            else:
                # Используем оригинальные калории
                final_calories = original_calories
                calories_display = f"{original_calories} ккал"
            
            # Обновляем сохраненные данные
            context.user_data['original_analysis'] = combined_analysis
            context.user_data['original_calories'] = final_calories
            context.user_data['calories_display'] = calories_display
            
            # Очищаем состояние ожидания дополнительного текста
            context.user_data.pop('waiting_for_additional_text', None)
            
            # Показываем обновленный результат с кнопками
            cleaned_result = clean_markdown_text(combined_analysis)
            result_text = f"**🍽️ {context.user_data.get('meal_name_name', 'Прием пищи')}**\n\n{cleaned_result}\n\n📊 **Калорийность:** {calories_display}"
            
            await processing_msg.edit_text(
                result_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_analysis")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                ]),
                parse_mode='Markdown'
            )
        else:
            # Если анализ не удался, показываем ошибку
            await processing_msg.edit_text(
                "❌ **Не удалось обработать дополнение**\n\n"
                "Попробуйте отправить более конкретное описание или нажмите 'Все верно?' для сохранения оригинального анализа.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_analysis")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                ]),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing additional text: {e}")
        await processing_msg.edit_text(
            "❌ **Ошибка обработки**\n\n"
            "Не удалось обработать дополнение. Попробуйте еще раз или нажмите 'Все верно?' для сохранения оригинального анализа.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_analysis")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
            ]),
            parse_mode='Markdown'
        )

__all__.append('handle_additional_text_analysis')

async def handle_check_additional_text_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик дополнительного текста для дополнения анализа фото (режим проверки)"""
    user = update.effective_user
    message = update.message
    additional_text = message.text.strip() if message.text else ""
    
    if not additional_text:
        await message.reply_text(
            "❌ Ошибка: пустое описание. Пожалуйста, отправьте текстовое описание с уточнениями.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
            ])
        )
        return
    
    # Получаем оригинальный анализ
    original_analysis = context.user_data.get('original_analysis', '')
    original_calories = context.user_data.get('original_calories', 0)
    original_dish_name = context.user_data.get('original_dish_name', 'Блюдо по фото')
    
    logger.info(f"Original analysis length: {len(original_analysis) if original_analysis else 0}")
    logger.info(f"Additional text: '{additional_text}'")
    
    if not original_analysis or not original_analysis.strip():
        logger.error(f"Original analysis is empty or None: '{original_analysis}'")
        await message.reply_text(
            "❌ Ошибка: данные анализа не найдены. Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )
        return
    
    # Отправляем сообщение о начале обработки
    processing_msg = await message.reply_text(
        "🔄 **Обрабатываю дополнение...**\n\n"
        "Анализирую уточнения с помощью ИИ модели...",
        parse_mode='Markdown'
    )
    
    try:
        # Создаем комбинированный запрос
        combined_prompt = f"Исходный анализ фото:\n{original_analysis}\n\nДополнительная информация от пользователя:\n{additional_text}\n\nНа основе исходного анализа и дополнительной информации, предоставь уточненный расчет калорий и БЖУ."
        
        logger.info(f"Combined prompt length: {len(combined_prompt)}")
        logger.info(f"Combined prompt preview: {combined_prompt[:200]}...")
        
        # Анализируем дополнительный текст с помощью специальной функции
        additional_analysis = await analyze_food_supplement(combined_prompt)
        
        if additional_analysis and is_valid_analysis(additional_analysis):
            # Объединяем оригинальный анализ с дополнительным
            combined_analysis = f"{original_analysis}\n\n**📝 Дополнения:**\n{additional_text}\n\n**🔄 Уточненный расчет:**\n{additional_analysis}"
            
            # Извлекаем новые калории из дополненного анализа
            new_calories = extract_calories_from_analysis(additional_analysis)
            if new_calories and new_calories > 0:
                # Используем новые калории
                final_calories = new_calories
                calories_display = f"{original_calories} → {new_calories} ккал"
            else:
                # Используем оригинальные калории
                final_calories = original_calories
                calories_display = f"{original_calories} ккал"
            
            # Обновляем сохраненные данные
            context.user_data['original_analysis'] = combined_analysis
            context.user_data['original_calories'] = final_calories
            context.user_data['calories_display'] = calories_display
            
            # Очищаем состояние ожидания дополнительного текста
            context.user_data.pop('waiting_for_check_additional_text', None)
            
            # Показываем обновленный результат с кнопками
            cleaned_result = clean_markdown_text(combined_analysis)
            result_text = f"🔍 **Анализ калорий**\n\n{cleaned_result}\n\n📊 **Калорийность:** {calories_display}\n\nℹ️ **Данные НЕ будут сохранены в статистику**"
            
            await processing_msg.edit_text(
                result_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_check_analysis")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                ]),
                parse_mode='Markdown'
            )
        else:
            # Если анализ не удался, показываем ошибку
            await processing_msg.edit_text(
                "❌ **Не удалось обработать дополнение**\n\n"
                "Попробуйте отправить более конкретное описание или нажмите 'Все верно?' для показа оригинального анализа.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_check_analysis")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                ]),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing additional text: {e}")
        await processing_msg.edit_text(
            "❌ **Ошибка обработки**\n\n"
            "Не удалось обработать дополнение. Попробуйте еще раз или нажмите 'Все верно?' для показа оригинального анализа.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_check_analysis")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
            ]),
            parse_mode='Markdown'
        )

__all__.append('handle_check_additional_text_analysis')

async def handle_confirm_photo_text_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Все верно?' для режима добавления блюда (фото + текст)"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Получаем сохраненные данные анализа
        original_analysis = context.user_data.get('original_analysis')
        original_calories = context.user_data.get('original_calories')
        original_dish_name = context.user_data.get('original_dish_name')
        
        if not original_analysis:
            await query.edit_message_text(
                "❌ Ошибка: данные анализа не найдены. Попробуйте еще раз.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
                ])
            )
            return
        
        # Получаем данные из контекста (если есть дополнения) или извлекаем из анализа
        from services.food_analysis_service import extract_macros_from_analysis, clean_markdown_text, extract_dish_name_from_analysis
        
        # Проверяем, есть ли сохраненные БЖУ в контексте (после дополнения)
        if 'original_protein' in context.user_data:
            calories = context.user_data.get('original_calories', 0)
            protein = context.user_data.get('original_protein', 0)
            fat = context.user_data.get('original_fat', 0)
            carbs = context.user_data.get('original_carbs', 0)
            dish_name = context.user_data.get('original_dish_name', 'Блюдо')
        else:
            # Извлекаем данные из анализа
            calories, protein, fat, carbs = extract_macros_from_analysis(original_analysis)
            dish_name = extract_dish_name_from_analysis(original_analysis) or original_dish_name
        
        # Получаем выбранный прием пищи
        meal_type = context.user_data.get('meal_name', 'meal_breakfast')
        meal_name = context.user_data.get('meal_name_name', 'Завтрак')
        
        # Сохраняем в базу данных
        from database import add_meal
        success = add_meal(
            telegram_id=user.id,
            meal_type=meal_type,
            meal_name=meal_name,
            dish_name=dish_name,
            calories=calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
            analysis_type="photo_text"
        )
        
        if success:
            # Очищаем состояния
            context.user_data.pop('waiting_for_photo_text_confirmation', None)
            context.user_data.pop('waiting_for_photo_text', None)
            context.user_data.pop('waiting_for_photo_text_additional', None)
            context.user_data.pop('original_analysis', None)
            context.user_data.pop('original_calories', None)
            context.user_data.pop('original_dish_name', None)
            context.user_data.pop('original_protein', None)
            context.user_data.pop('original_fat', None)
            context.user_data.pop('original_carbs', None)
            context.user_data.pop('save_mode', None)
            
            cleaned_result = clean_markdown_text(original_analysis)
            result_text = f"✅ Блюдо добавлено в статистику!\n\n🍽️ {meal_name}\n\n{cleaned_result}"
            
            await query.edit_message_text(
                result_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]
                ])
            )
        else:
            await query.edit_message_text(
                "❌ Ошибка сохранения\n\n"
                "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
                ])
            )
            
    except Exception as e:
        logger.error(f"Error in handle_confirm_photo_text_analysis: {e}")
        await query.edit_message_text(
            "❌ Ошибка обработки\n\n"
            "Произошла ошибка при сохранении данных. Попробуйте еще раз.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
            ])
        )

__all__.append('handle_confirm_photo_text_analysis')

async def handle_add_to_photo_text_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Дополнить' для режима добавления блюда (фото + текст)"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, не использовал ли пользователь уже возможность дополнения
    if context.user_data.get('photo_text_additional_used', False):
        await query.edit_message_text(
            "⚠️ **Дополнение уже использовано**\n\n"
            "Можно дополнить анализ только один раз.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_photo_text_analysis")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
            ])
        )
        return
    
    # Устанавливаем состояние ожидания дополнительного текста
    context.user_data['waiting_for_photo_text_additional'] = True
    context.user_data['photo_text_additional_used'] = True
    
    await query.edit_message_text(
        "✏️ **Дополните анализ**\n\n"
        "Отправьте текстовое описание с уточнениями:\n"
        "• Количество порций\n"
        "• Способ приготовления\n"
        "• Дополнительные ингредиенты\n"
        "• Размер порции\n\n"
        "⚠️ **Можно дополнить анализ только один раз!**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_add_to_photo_text_analysis')

async def handle_confirm_photo_text_check_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Все верно?' для режима проверки калорий (фото + текст)"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем состояния
    context.user_data.pop('waiting_for_photo_text_confirmation', None)
    context.user_data.pop('waiting_for_photo_text', None)
    context.user_data.pop('waiting_for_photo_text_additional', None)
    context.user_data.pop('waiting_for_photo_text_check_additional', None)
    context.user_data.pop('original_analysis', None)
    context.user_data.pop('original_calories', None)
    context.user_data.pop('original_dish_name', None)
    context.user_data.pop('original_protein', None)
    context.user_data.pop('original_fat', None)
    context.user_data.pop('original_carbs', None)
    context.user_data.pop('check_mode', None)
    
    await query.edit_message_text(
        "✅ **Анализ завершен**\n\n"
        "Спасибо за использование функции проверки калорий!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
        ])
    )

__all__.append('handle_confirm_photo_text_check_analysis')

async def handle_add_to_photo_text_check_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Дополнить' для режима проверки калорий (фото + текст)"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, не использовал ли пользователь уже возможность дополнения
    if context.user_data.get('photo_text_check_additional_used', False):
        await query.edit_message_text(
            "⚠️ **Дополнение уже использовано**\n\n"
            "Можно дополнить анализ только один раз.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_photo_text_check_analysis")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
            ])
        )
        return
    
    # Устанавливаем состояние ожидания дополнительного текста
    context.user_data['waiting_for_photo_text_check_additional'] = True
    context.user_data['photo_text_check_additional_used'] = True
    
    await query.edit_message_text(
        "✏️ **Дополните анализ**\n\n"
        "Отправьте текстовое описание с уточнениями:\n"
        "• Количество порций\n"
        "• Способ приготовления\n"
        "• Дополнительные ингредиенты\n"
        "• Размер порции\n\n"
        "⚠️ **Можно дополнить анализ только один раз!**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_add_to_photo_text_check_analysis')

async def handle_photo_text_additional_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик дополнительного текста для фото + текст (режим добавления)"""
    message = update.message
    user = update.effective_user
    
    try:
        additional_text = message.text.strip() if message.text else ""
        
        if not additional_text:
            await message.reply_text(
                "❌ Ошибка: пустое описание. Пожалуйста, отправьте текстовое описание с уточнениями.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                ])
            )
            return
        
        # Получаем оригинальный анализ
        original_analysis = context.user_data.get('original_analysis')
        if not original_analysis:
            await message.reply_text(
                "❌ Ошибка: данные анализа не найдены. Попробуйте еще раз.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
                ])
            )
            return
        
        # Создаем уточненный запрос
        from api_client import api_client
        
        # Сначала анализируем фото (используем кэш)
        photo_analysis = original_analysis
        
        # Создаем объединенный промпт
        combined_prompt = f"""
Исходный анализ фото:
{photo_analysis}

Дополнительная информация от пользователя:
{additional_text}

На основе анализа фото и дополнительной информации пользователя, предоставь уточненный анализ в следующем формате:

🍽️ Анализ блюда:

Название: [название блюда]
Вес: [общий вес блюда]г
Калорийность: [ОБЩАЯ калорийность для всего количества] ккал

📊 БЖУ на 100г:
• Белки: [количество]г
• Жиры: [количество]г  
• Углеводы: [количество]г

📈 Общее БЖУ в блюде:
• Белки: [общее количество]г
• Жиры: [общее количество]г
• Углеводы: [общее количество]г

Учти дополнительную информацию пользователя для более точного определения веса, ингредиентов и способа приготовления.
"""
        
        # Отправляем уточненный запрос
        async with api_client:
            refined_analysis = await api_client.analyze_photo_with_text(None, combined_prompt)
        
        if refined_analysis:
            # Обновляем данные анализа
            context.user_data['original_analysis'] = refined_analysis
            
            # Извлекаем данные из уточненного анализа
            from services.food_analysis_service import extract_macros_from_analysis, clean_markdown_text, extract_dish_name_from_analysis
            
            calories, protein, fat, carbs = extract_macros_from_analysis(refined_analysis)
            dish_name = extract_dish_name_from_analysis(refined_analysis) or 'Блюдо'
            
            # Обновляем сохраненные данные
            context.user_data['original_calories'] = calories
            context.user_data['original_dish_name'] = dish_name
            context.user_data['original_protein'] = protein
            context.user_data['original_fat'] = fat
            context.user_data['original_carbs'] = carbs
            
            # Показываем уточненный результат
            cleaned_result = clean_markdown_text(refined_analysis)
            result_text = f"✏️ Уточненный анализ\n\n{cleaned_result}"
            
            await message.reply_text(
                result_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_photo_text_analysis")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                ])
            )
        else:
            # Если анализ не удался, показываем ошибку
            await message.reply_text(
                "❌ Не удалось обработать дополнение\n\n"
                "Попробуйте отправить более конкретное описание или нажмите 'Все верно?' для сохранения оригинального анализа.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_photo_text_analysis")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                ])
            )
            
    except Exception as e:
        logger.error(f"Error processing photo text additional analysis: {e}")
        await message.reply_text(
            "❌ Ошибка обработки\n\n"
            "Не удалось обработать дополнение. Попробуйте еще раз или нажмите 'Все верно?' для сохранения оригинального анализа.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_photo_text_analysis")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
            ])
        )

__all__.append('handle_photo_text_additional_analysis')

async def handle_photo_text_check_additional_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик дополнительного текста для фото + текст (режим проверки)"""
    message = update.message
    user = update.effective_user
    
    try:
        additional_text = message.text.strip() if message.text else ""
        
        if not additional_text:
            await message.reply_text(
                "❌ Ошибка: пустое описание. Пожалуйста, отправьте текстовое описание с уточнениями.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                ])
            )
            return
        
        # Получаем оригинальный анализ
        original_analysis = context.user_data.get('original_analysis')
        if not original_analysis:
            await message.reply_text(
                "❌ Ошибка: данные анализа не найдены. Попробуйте еще раз.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
                ])
            )
            return
        
        # Создаем уточненный запрос
        from api_client import api_client
        
        # Сначала анализируем фото (используем кэш)
        photo_analysis = original_analysis
        
        # Создаем объединенный промпт
        combined_prompt = f"""
Исходный анализ фото:
{photo_analysis}

Дополнительная информация от пользователя:
{additional_text}

На основе анализа фото и дополнительной информации пользователя, предоставь уточненный анализ в следующем формате:

🍽️ Анализ блюда:

Название: [название блюда]
Вес: [общий вес блюда]г
Калорийность: [ОБЩАЯ калорийность для всего количества] ккал

📊 БЖУ на 100г:
• Белки: [количество]г
• Жиры: [количество]г  
• Углеводы: [количество]г

📈 Общее БЖУ в блюде:
• Белки: [общее количество]г
• Жиры: [общее количество]г
• Углеводы: [общее количество]г

Учти дополнительную информацию пользователя для более точного определения веса, ингредиентов и способа приготовления.
"""
        
        # Отправляем уточненный запрос
        async with api_client:
            refined_analysis = await api_client.analyze_photo_with_text(None, combined_prompt)
        
        if refined_analysis:
            # Обновляем данные анализа
            context.user_data['original_analysis'] = refined_analysis
            
            # Извлекаем данные из уточненного анализа
            from services.food_analysis_service import extract_macros_from_analysis, clean_markdown_text, extract_dish_name_from_analysis
            
            calories, protein, fat, carbs = extract_macros_from_analysis(refined_analysis)
            dish_name = extract_dish_name_from_analysis(refined_analysis) or 'Блюдо'
            
            # Обновляем сохраненные данные
            context.user_data['original_calories'] = calories
            context.user_data['original_dish_name'] = dish_name
            context.user_data['original_protein'] = protein
            context.user_data['original_fat'] = fat
            context.user_data['original_carbs'] = carbs
            
            # Показываем уточненный результат
            cleaned_result = clean_markdown_text(refined_analysis)
            result_text = f"✏️ **Уточненный анализ**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ будут сохранены в статистику**"
            
            await message.reply_text(
                result_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_photo_text_check_analysis")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                ]),
                parse_mode='Markdown'
            )
        else:
            # Если анализ не удался, показываем ошибку
            await message.reply_text(
                "❌ **Не удалось обработать дополнение**\n\n"
                "Попробуйте отправить более конкретное описание или нажмите 'Все верно?' для показа оригинального анализа.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_photo_text_check_analysis")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                ]),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing photo text check additional analysis: {e}")
        await message.reply_text(
            "❌ **Ошибка обработки**\n\n"
            "Не удалось обработать дополнение. Попробуйте еще раз или нажмите 'Все верно?' для показа оригинального анализа.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_photo_text_check_analysis")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
            ]),
            parse_mode='Markdown'
        )

__all__.append('handle_photo_text_check_additional_analysis')

async def handle_send_location_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Отправить геолокацию'"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📍 **Отправьте геолокацию**\n\n"
        "Нажмите на кнопку 'Отправить геолокацию' в Telegram или отправьте координаты.\n\n"
        "Это поможет автоматически определить ваш часовой пояс.",
        parse_mode='Markdown'
    )

async def handle_manual_timezone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Выбрать часовой пояс вручную'"""
    query = update.callback_query
    await query.answer()
    
    # Создаем клавиатуру с выбором полушария
    from constants import TIMEZONE_HEMISPHERES
    
    keyboard = []
    
    # Кнопки для выбора полушария
    keyboard.append([InlineKeyboardButton("🌍 Западное полушарие", callback_data="tz_hemisphere_western")])
    keyboard.append([InlineKeyboardButton("🌏 Восточное полушарие", callback_data="tz_hemisphere_eastern")])
    
    # Кнопка "Другие часовые пояса" для полного списка
    keyboard.append([InlineKeyboardButton("🌍 Другие часовые пояса", callback_data="tz_other")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🌍 **Выберите ваш часовой пояс:**\n\n"
        "Это необходимо для корректной отправки напоминаний о приемах пищи.\n\n"
        "Выберите ваше полушарие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик геолокации для определения часового пояса"""
    user = update.effective_user
    message = update.message
    
    # Проверяем, идет ли процесс регистрации
    if context.user_data.get('registration_step') != 'location':
        await message.reply_text("❌ Геолокация не требуется в данный момент.")
        return
    
    if not message.location:
        await message.reply_text("❌ Пожалуйста, отправьте геолокацию.")
        return
    
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    try:
        # Определяем часовой пояс по координатам
        timezone = get_timezone_from_coordinates(latitude, longitude)
        
        if timezone:
            # Сохраняем часовой пояс в данных пользователя
            user_data = context.user_data['user_data']
            user_data['timezone'] = timezone
            
            # Переходим к завершению регистрации
            await complete_registration(update, context)
        else:
            # Если не удалось определить часовой пояс, предлагаем выбрать вручную
            keyboard = [
                [InlineKeyboardButton("🌍 Выбрать часовой пояс вручную", callback_data="manual_timezone")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                "❌ **Не удалось определить часовой пояс**\n\n"
                "Попробуйте выбрать часовой пояс вручную:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing location: {e}")
        await message.reply_text(
            "❌ Ошибка при обработке геолокации. Попробуйте выбрать часовой пояс вручную.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌍 Выбрать часовой пояс вручную", callback_data="manual_timezone")]
            ])
        )

def get_timezone_from_coordinates(latitude: float, longitude: float) -> str:
    """Определяет часовой пояс по координатам"""
    try:
        import pytz
        from timezonefinder import TimezoneFinder
        
        tf = TimezoneFinder()
        timezone_name = tf.timezone_at(lat=latitude, lng=longitude)
        
        if timezone_name:
            # Проверяем, что часовой пояс валидный
            try:
                pytz.timezone(timezone_name)
                return timezone_name
            except pytz.exceptions.UnknownTimeZoneError:
                pass
        
        # Если не удалось определить точный часовой пояс, используем приблизительный
        # Определяем UTC offset на основе долготы
        utc_offset = int(longitude / 15)
        
        # Ограничиваем offset от -12 до +14
        utc_offset = max(-12, min(14, utc_offset))
        
        # Возвращаем приблизительный часовой пояс
        if utc_offset == 0:
            return "Europe/London"
        elif utc_offset > 0:
            return f"Etc/GMT-{utc_offset}"
        else:
            return f"Etc/GMT+{abs(utc_offset)}"
            
    except Exception as e:
        logger.error(f"Error determining timezone from coordinates: {e}")
        return None

async def complete_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает процесс регистрации"""
    from handlers.registration import calculate_daily_calories, calculate_target_calories
    from handlers.menu import get_main_menu_keyboard
    from handlers.subscription import check_subscription_access, get_subscription_message
    from constants import GOALS
    
    user_data = context.user_data['user_data']
    
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
    
    # Рассчитываем целевые БЖУ
    from utils.macros_calculator import calculate_daily_macros
    
    target_macros = calculate_daily_macros(
        weight=user_data['weight'],
        activity_level=user_data['activity_level'],
        goal=user_data['goal'],
        target_calories=user_data['target_calories']
    )
    
    # Сохраняем пользователя в базу данных с БЖУ
    from database import get_db_connection
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (
                    telegram_id, name, gender, age, height, weight, 
                    activity_level, goal, daily_calories, target_calories,
                    target_protein, target_fat, target_carbs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data['telegram_id'],
                user_data['name'],
                user_data['gender'],
                user_data['age'],
                user_data['height'],
                user_data['weight'],
                user_data['activity_level'],
                user_data['goal'],
                user_data['daily_calories'],
                user_data['target_calories'],
                target_macros['protein'],
                target_macros['fat'],
                target_macros['carbs']
            ))
            conn.commit()
        success = True
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        success = False
    
    if not success:
        await update.message.reply_text(
            "❌ Произошла ошибка при сохранении данных. Попробуйте регистрацию заново."
        )
        return
    
    # Обновляем часовой пояс пользователя
    from database import update_user_timezone
    update_user_timezone(user_data['telegram_id'], user_data['timezone'])
    
    # Очищаем данные регистрации
    context.user_data.pop('registration_step', None)
    context.user_data.pop('user_data', None)
    
    # Используем полное главное меню
    reply_markup = get_main_menu_keyboard_for_user(update)
    
    # Получаем информацию о подписке
    access_info = check_subscription_access(user_data['telegram_id'])
    subscription_msg = get_subscription_message(access_info)
    
    # Формируем сообщение с информацией о целях
    goal_text = GOALS[user_data['goal']]
    goal_emoji = "📉" if user_data['goal'] == 'lose_weight' else "⚖️" if user_data['goal'] == 'maintain' else "📈"
    
    # Получаем читаемое имя часового пояса
    from constants import TIMEZONES
    timezone_name = TIMEZONES.get(user_data['timezone'], user_data['timezone'])
    
    # Показываем приветственное сообщение с БЖУ
    welcome_text = (
        f"Привет {user_data['name']}, ✅ **Регистрация завершена!**\n\n"
        f"🎯 **Ваша цель:** {goal_emoji} {goal_text}\n"
        f"📊 **Расчетная норма:** {daily_calories} ккал\n"
        f"🎯 **Целевая норма:** {target_calories} ккал\n"
        f"🌍 **Часовой пояс:** {timezone_name}\n\n"
        f"🥗 **Суточная норма БЖУ:**\n"
        f"• Белки: {target_macros['protein']:.1f}г\n"
        f"• Жиры: {target_macros['fat']:.1f}г\n"
        f"• Углеводы: {target_macros['carbs']:.1f}г\n\n"
        f"{subscription_msg}\n\n"
        f"Выберите действие:"
    )
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        # Для callback query
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

__all__.append('handle_send_location_callback')
__all__.append('handle_manual_timezone_callback')
__all__.append('handle_location')
__all__.append('get_timezone_from_coordinates')
__all__.append('complete_registration')

