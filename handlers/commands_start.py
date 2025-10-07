# Auto-generated module for commands_start handlers extracted from bot_functions.py
from ._shared import *  # imports, constants, helpers
import bot_functions as bf  # for cross-module handler calls

__all__ = []

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню для зарегистрированных пользователей"""
    return await show_main_menu_from_handler(update, context)

__all__.append('show_main_menu')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    return await start_command_from_handler(update, context)

__all__.append('start_command')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    return await help_command_from_handler(update, context)

__all__.append('help_command')

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

__all__.append('handle_menu_from_meal_selection')

async def show_admin_manage_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id: int, user_data: Optional[Tuple[Any, ...]]):
    """Показывает меню управления подпиской для конкретного пользователя"""
    # Получаем информацию о подписке
    subscription_info = check_user_subscription(telegram_id)
    
    # Формируем текст о подписке
    subscription_text = ""
    if subscription_info['is_active']:
        if subscription_info['type'] == 'trial':
            subscription_text = f"🆓 <b>Триальный период</b>\nДоступен до: {subscription_info['expires_at']}"
        elif subscription_info['type'] == 'premium':
            if subscription_info['expires_at']:
                subscription_text = f"⭐ <b>Премиум подписка</b>\nДействует до: {subscription_info['expires_at']}"
            else:
                subscription_text = "⭐ <b>Премиум подписка</b>\nБез ограничений"
    else:
        if subscription_info['type'] == 'trial_expired':
            subscription_text = f"❌ <b>Триальный период истек</b>\nИстек: {subscription_info['expires_at']}"
        elif subscription_info['type'] == 'premium_expired':
            subscription_text = f"❌ <b>Премиум подписка истекла</b>\nИстекла: {subscription_info['expires_at']}"
        else:
            subscription_text = "❌ <b>Нет активной подписки</b>"
    
    # Экранируем специальные символы для Markdown
    safe_name = str(user_data[2]).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
    safe_date = str(user_data[16] if len(user_data) > 16 else 'Неизвестно').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
    
    manage_text = f"""
👤 <b>Управление подпиской пользователя</b>

📝 <b>Имя:</b> {safe_name}
🆔 <b>Telegram ID:</b> {telegram_id}
📅 <b>Дата регистрации:</b> {safe_date}

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
        parse_mode='HTML'
    )

__all__.append('show_admin_manage_subscription_menu')

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

__all__.append('show_subscription_purchase_menu')

