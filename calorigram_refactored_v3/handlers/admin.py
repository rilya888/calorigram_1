# Auto-generated module for admin handlers extracted from bot_functions.py
import bot_functions as bf  # for cross-module handler calls

# Импортируем необходимые функции напрямую
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db_connection, get_user_count, get_meals_count, get_daily_stats, get_all_users_for_admin, get_all_users_for_broadcast, get_user_by_telegram_id, activate_premium_subscription
from constants import ADMIN_CALLBACKS, GOALS
from config import ADMIN_IDS
from logging_config import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)

# Импортируем функции из _shared
def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return user_id in ADMIN_IDS

def check_subscription_access(telegram_id: int) -> dict:
    """Проверяет доступ пользователя к функциям бота"""
    from handlers.subscription import check_subscription_access as check_access
    return check_access(telegram_id)

def get_subscription_message(access_info: dict) -> str:
    """Возвращает сообщение о статусе подписки"""
    from handlers.subscription import get_subscription_message as get_msg
    return get_msg(access_info)

def get_main_menu_keyboard(user_id=None):
    """Создает клавиатуру главного меню"""
    from handlers.menu import get_main_menu_keyboard as get_keyboard
    return get_keyboard(user_id)

def check_user_registration(user_id: int):
    """Проверяет, зарегистрирован ли пользователь"""
    from handlers.registration import check_user_registration as check_reg
    return check_reg(user_id)

def calculate_daily_calories(age, height, weight, gender: str, activity_level: str) -> int:
    """Рассчитывает суточную норму калорий"""
    from handlers.registration import calculate_daily_calories as calc_cal
    return calc_cal(age, height, weight, gender, activity_level)

def get_daily_meals_by_type(user_id: int, date: str = None):
    """Получает калории по типам приемов пищи за день"""
    from database import get_daily_meals_by_type as get_meals
    return get_meals(user_id, date)

def get_weekly_meals_by_type(user_id: int):
    """Получает калории по дням недели за последние 7 дней"""
    from database import get_weekly_meals_by_type as get_week
    return get_week(user_id)

def send_broadcast_message(bot, message_text: str, admin_id: int) -> dict:
    """Отправляет рассылку всем пользователям"""
    from handlers._shared import send_broadcast_message as send_broadcast
    return send_broadcast(bot, message_text, admin_id)

def get_bot_star_balance():
    """Получает текущий баланс Stars бота"""
    from handlers._shared import get_bot_star_balance as get_balance
    return get_balance()

__all__ = []

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
    
    await bf.show_admin_panel(update, context)

__all__.append('admin_command')

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

__all__.append('show_admin_panel')

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

__all__.append('handle_admin_stats_callback')

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

__all__.append('handle_admin_users_callback')

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

__all__.append('handle_admin_broadcast_callback')

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

__all__.append('handle_broadcast_create_callback')

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

__all__.append('handle_broadcast_stats_callback')

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

__all__.append('handle_broadcast_confirm_callback')

async def handle_broadcast_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отмены рассылки"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем состояние
    context.user_data.pop('waiting_for_broadcast_text', None)
    context.user_data.pop('broadcast_text', None)
    
    # Возвращаемся к меню рассылки
    await bf.handle_admin_broadcast_callback(update, context)

__all__.append('handle_broadcast_cancel_callback')

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

__all__.append('handle_broadcast_text_input')

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

__all__.append('handle_admin_back_callback')

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

__all__.append('handle_admin_subscriptions_callback')

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

__all__.append('handle_admin_check_subscription_callback')

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
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Вернуться в админку", callback_data="admin_panel")]
            ]),
            parse_mode='Markdown'
        )
    else:
        await query.message.reply_text(
            f"❌ **Ошибка активации триального периода!**\n\n"
            f"Пользователь {telegram_id} не найден или произошла ошибка базы данных.",
            parse_mode='Markdown'
        )

__all__.append('handle_admin_activate_trial_callback')

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
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Вернуться в админку", callback_data="admin_panel")]
            ]),
            parse_mode='Markdown'
        )
    else:
        await query.message.reply_text(
            f"❌ **Ошибка активации премиум подписки!**\n\n"
            f"Пользователь {telegram_id} не найден или произошла ошибка базы данных.",
            parse_mode='Markdown'
        )

__all__.append('handle_admin_activate_premium_callback')

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
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Вернуться в админку", callback_data="admin_panel")]
                    ]),
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

__all__.append('handle_admin_deactivate_subscription_callback')

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
        await bf.show_admin_manage_subscription_menu(update, context, telegram_id, user_data)
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Неверный формат Telegram ID!**\n\n"
            "Пожалуйста, введите числовой ID пользователя (например: 123456789)",
            parse_mode='Markdown'
        )

__all__.append('handle_admin_telegram_id_input')

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

__all__.append('handle_statistics_callback')

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
                goal = user_data[9] if len(user_data) > 9 else 'maintain'
                # Безопасное получение целевых калорий
                try:
                    if len(user_data) > 10 and user_data[10] and str(user_data[10]).isdigit():
                        target_calories = int(user_data[10])
                    else:
                        target_calories = daily_norm
                except (ValueError, TypeError):
                    target_calories = daily_norm
                
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

__all__.append('handle_stats_today_callback')

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
                goal = user_data[9] if len(user_data) > 9 else 'maintain'
                # Безопасное получение целевых калорий
                try:
                    if len(user_data) > 10 and user_data[10] and str(user_data[10]).isdigit():
                        target_calories = int(user_data[10])
                    else:
                        target_calories = daily_norm
                except (ValueError, TypeError):
                    target_calories = daily_norm
                
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

__all__.append('handle_stats_yesterday_callback')

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
                goal = user_data[9] if len(user_data) > 9 else 'maintain'
                # Безопасное получение целевых калорий
                try:
                    if len(user_data) > 10 and user_data[10] and str(user_data[10]).isdigit():
                        target_calories = int(user_data[10])
                    else:
                        target_calories = daily_norm
                except (ValueError, TypeError):
                    target_calories = daily_norm
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

__all__.append('handle_stats_week_callback')

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

__all__.append('handle_admin_star_balance_callback')

async def handle_admin_meals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик просмотра последних приемов пищи"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем права админа
    if user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем последние 20 приемов пищи
            cursor.execute('''
                SELECT 
                    m.id,
                    m.telegram_id,
                    u.name,
                    m.meal_type,
                    m.meal_name,
                    m.calories,
                    m.created_at
                FROM meals m
                JOIN users u ON m.telegram_id = u.telegram_id
                ORDER BY m.created_at DESC
                LIMIT 20
            ''')
            
            meals = cursor.fetchall()
            
            if not meals:
                await query.message.reply_text(
                    "🍽️ **Последние приемы пищи**\n\n"
                    "📝 Записей о еде пока нет.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Админ панель", callback_data=ADMIN_CALLBACKS['admin_panel'])]
                    ]),
                    parse_mode='Markdown'
                )
                return
            
            # Формируем сообщение
            meals_text = "🍽️ **Последние приемы пищи**\n\n"
            
            for meal in meals:
                meal_id, telegram_id, name, meal_type, meal_name, calories, created_at = meal
                
                # Определяем тип приема пищи
                meal_type_emoji = {
                    'meal_breakfast': '🌅',
                    'meal_lunch': '🌞', 
                    'meal_dinner': '🌙',
                    'meal_snack': '🍎'
                }.get(meal_type, '🍽️')
                
                # Форматируем дату
                try:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = created_dt.strftime('%d.%m.%Y %H:%M')
                except:
                    formatted_date = created_at
                
                meals_text += f"{meal_type_emoji} **{name}** ({telegram_id})\n"
                meals_text += f"   {meal_name} - {calories} ккал\n"
                meals_text += f"   📅 {formatted_date}\n\n"
            
            # Добавляем кнопку "Показать еще" если записей много
            keyboard = [[InlineKeyboardButton("🔙 Админ панель", callback_data=ADMIN_CALLBACKS['admin_panel'])]]
            
            if len(meals) >= 20:
                keyboard.insert(0, [InlineKeyboardButton("📄 Показать еще", callback_data="admin_meals_more")])
            
            await query.message.reply_text(
                meals_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in handle_admin_meals_callback: {e}")
        await query.message.reply_text(
            "❌ Произошла ошибка при получении данных о приемах пищи. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Админ панель", callback_data=ADMIN_CALLBACKS['admin_panel'])]
            ])
        )

__all__.append('handle_admin_meals_callback')

