# Auto-generated module for profile handlers extracted from bot_functions.py
from ._shared import *  # imports, constants, helpers
import bot_functions as bf  # for cross-module handler calls

__all__ = []

async def send_not_registered_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет сообщение о том, что пользователь не зарегистрирован"""
    message = ERROR_MESSAGES['user_not_registered']
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(message)
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(message)

__all__.append('send_not_registered_message')

async def handle_timezone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора часового пояса"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, есть ли данные пользователя
    if 'user_data' not in context.user_data:
        await query.message.reply_text(
            "❌ Ошибка: данные регистрации не найдены.\n"
            "Пожалуйста, начните регистрацию заново с помощью /register"
        )
        return
    
    user_data = context.user_data['user_data']
    
    # Если выбран "Другие часовые пояса", показываем расширенный список
    if query.data == 'tz_other':
        from constants import TIMEZONES
        
        keyboard = []
        for tz_key, tz_name in TIMEZONES.items():
            keyboard.append([InlineKeyboardButton(tz_name, callback_data=f"tz_{tz_key}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🌍 **Все доступные часовые пояса:**\n\n"
            "Выберите ваш регион:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Если выбран полушарие
    if query.data.startswith('tz_hemisphere_'):
        from constants import TIMEZONE_HEMISPHERES
        
        hemisphere_key = query.data.replace('tz_hemisphere_', '')
        if hemisphere_key in TIMEZONE_HEMISPHERES:
            hemisphere = TIMEZONE_HEMISPHERES[hemisphere_key]
            
            # Показываем часовые пояса в выбранном полушарии
            keyboard = []
            for offset_key, group in hemisphere['timezones'].items():
                button_text = f"{group['name']} - {group['description']}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"tz_group_{offset_key}")])
            
            # Кнопка "Назад"
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="tz_back_to_hemispheres")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🌍 **{hemisphere['name']}**\n\n"
                f"{hemisphere['description']}\n\n"
                "Выберите ваш часовой пояс:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        return
    
    # Если выбран часовой пояс из группы
    if query.data.startswith('tz_group_'):
        from constants import TIMEZONE_GROUPS, TIMEZONES
        
        group_key = query.data.replace('tz_group_', '')
        if group_key in TIMEZONE_GROUPS:
            group = TIMEZONE_GROUPS[group_key]
            
            # Показываем города в этой группе
            keyboard = []
            for tz_key in group['timezones']:
                # Находим название города в старом списке TIMEZONES
                tz_name = None
                for old_tz_key, old_tz_name in TIMEZONES.items():
                    if old_tz_key == tz_key:
                        tz_name = old_tz_name
                        break
                
                if tz_name:
                    keyboard.append([InlineKeyboardButton(tz_name, callback_data=f"tz_{tz_key}")])
            
            # Кнопка "Назад"
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="tz_back_to_hemispheres")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🌍 **{group['name']} - {group['description']}**\n\n"
                "Выберите ваш город:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        return
    
    # Если нажата кнопка "Назад" к полушариям
    if query.data == 'tz_back_to_hemispheres':
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
        return
    
    # Извлекаем timezone из callback_data
    timezone = query.data.replace('tz_', '')
    user_data['timezone'] = timezone
    
    # Получаем имя пользователя
    name = user_data.get('name', 'Пользователь')
    
    # Вызываем complete_registration для завершения регистрации с БЖУ
    from handlers.misc import complete_registration
    await complete_registration(update, context)

__all__.append('handle_timezone_callback')

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /profile"""
    user = update.effective_user
    logger.info(f"Profile command called by user {user.id}")
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        user_data = check_user_registration(user.id)
        
        # Отладочная информация для разработки
        if TEST_MODE:
            logger.debug(f"user_data: {user_data}")
            if user_data:
                logger.debug(f"user_data length: {len(user_data)}")
                for i, value in enumerate(user_data):
                    logger.debug(f"user_data[{i}]: {value} (type: {type(value)})")
        
        if not user_data:
            await bf.send_not_registered_message(update, context)
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
        goal = user_data[9] if len(user_data) > 9 and user_data[9] else 'maintain'
        
        # Правильно определяем индекс целевой нормы калорий
        # user_data[8] - daily_calories, user_data[9] - goal, user_data[10] - target_calories
        if len(user_data) > 10 and user_data[10] and str(user_data[10]).isdigit():
            target_calories = int(user_data[10])
        else:
            target_calories = int(user_data[8])  # fallback to daily_calories
        
        # Формируем текст о цели
        goal_text = GOALS.get(goal, 'Держать себя в форме')
        goal_emoji = "📉" if goal == 'lose_weight' else "⚖️" if goal == 'maintain' else "📈"
        
        # Получаем часовой пояс из правильного поля (user_data[17])
        timezone = user_data[17] if len(user_data) > 17 else 'UTC'
        
        # Отладочная информация для разработки
        if TEST_MODE:
            logger.debug(f"user_data: {user_data}")
            logger.debug(f"timezone: {timezone} (type: {type(timezone)})")
        
        # Обрабатываем часовой пояс так же, как при регистрации
        from constants import TIMEZONES
        timezone_name = TIMEZONES.get(timezone, timezone)
        
        if TEST_MODE:
            logger.debug(f"timezone_name: {timezone_name}")
        
        # Получаем БЖУ из правильных колонок базы данных
        # user_data[11] = target_protein, user_data[12] = target_fat, user_data[13] = target_carbs
        target_protein = user_data[11] if len(user_data) > 11 and user_data[11] else 0.0
        target_fat = user_data[12] if len(user_data) > 12 and user_data[12] else 0.0
        target_carbs = user_data[13] if len(user_data) > 13 and user_data[13] else 0.0
        
        # Преобразуем в числа, если они строки
        try:
            target_protein = float(target_protein) if target_protein else 0.0
            target_fat = float(target_fat) if target_fat else 0.0
            target_carbs = float(target_carbs) if target_carbs else 0.0
        except (ValueError, TypeError):
            target_protein = 0.0
            target_fat = 0.0
            target_carbs = 0.0
        
        profile_text = f"""👤 Ваш профиль:

📝 Имя: {user_data[2]}
👤 Пол: {user_data[3]}
🎂 Возраст: {user_data[4]} лет
📏 Рост: {user_data[5]} см
⚖️ Вес: {user_data[6]} кг
🏃 Уровень активности: {user_data[7]}
🎯 Цель: {goal_emoji} {goal_text}
📊 Расчетная норма: {user_data[8]} ккал
🎯 Целевая норма: {target_calories} ккал

🥗 Суточная норма БЖУ:
• Белки: {target_protein:.1f}г
• Жиры: {target_fat:.1f}г
• Углеводы: {target_carbs:.1f}г

🌍 Часовой пояс: {timezone_name}

{subscription_text}"""
        
        # Создаем клавиатуру профиля с кнопкой статистики
        profile_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Статистика за сегодня", callback_data="stats_today")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
        ])
        
        await update.message.reply_text(profile_text, reply_markup=profile_keyboard)
    except Exception as e:
        logger.error(f"Error in profile_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении данных профиля. Попробуйте позже."
        )

__all__.append('profile_command')

async def addmeal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /addmeal"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if not existing_user:
            await bf.send_not_registered_message(update, context)
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

__all__.append('addmeal_command')

async def show_meal_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику по приемам пищи с БЖУ и прогресс-барами"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        user_data = check_user_registration(user.id)
        if not user_data:
            await bf.send_not_registered_message(update, context)
            return
        
        # Получаем данные за сегодня
        from database import get_daily_macros, get_daily_meals_by_type, get_user_target_macros
        from utils.progress_bars import create_calorie_progress_bar, create_macro_progress_bar, create_meal_breakdown
        from utils.macros_calculator import get_macro_recommendations
        
        current_macros = get_daily_macros(user.id)
        target_macros = get_user_target_macros(user.id)
        meals_data = get_daily_meals_by_type(user.id)
        
        # Создаем прогресс-бары
        calorie_bar = create_calorie_progress_bar(current_macros['calories'], target_macros['calories'])
        
        protein_bar = create_macro_progress_bar(
            current_macros['protein'], 
            target_macros['protein'], 
            "Белки", 
            "г"
        )
        
        fat_bar = create_macro_progress_bar(
            current_macros['fat'], 
            target_macros['fat'], 
            "Жиры", 
            "г"
        )
        
        carbs_bar = create_macro_progress_bar(
            current_macros['carbs'], 
            target_macros['carbs'], 
            "Углеводы", 
            "г"
        )
        
        # Создаем разбивку по приемам пищи
        meal_breakdown = create_meal_breakdown(meals_data)
        
        # Генерируем рекомендации
        recommendations = get_macro_recommendations(current_macros, target_macros)
        
        # Формируем сообщение
        stats_message = f"""📊 **Статистика за сегодня**

{calorie_bar}

🥗 **БЖУ:**
{protein_bar}
{fat_bar}
{carbs_bar}

{meal_breakdown}

💡 **Рекомендации:**
{recommendations}"""
        
        await query.edit_message_text(
            stats_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="profile")]
            ]),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing meal statistics: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при загрузке статистики. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="profile")]
            ])
        )

__all__.append('show_meal_statistics')