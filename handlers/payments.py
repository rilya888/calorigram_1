# Auto-generated module for payments handlers extracted from bot_functions.py
from ._shared import *
from database import is_payment_processed, mark_payment_processed  # imports, constants, helpers
import bot_functions as bf  # for cross-module handler calls
from handlers.menu import get_main_menu_keyboard_for_user

__all__ = []

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
                    reply_markup=get_main_menu_keyboard_for_user(update)
                )
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(
                    "❌ Вы не зарегистрированы в системе!\n"
                    "Используйте /register для регистрации.",
                    reply_markup=get_main_menu_keyboard_for_user(update)
                )
            return
        
        # Получаем информацию о подписке
        access_info = check_subscription_access(user.id)
        subscription_msg = get_subscription_message(access_info)
        
        # Проверяем, это команда или callback запрос
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                subscription_msg,
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                subscription_msg,
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error in subscription_command: {e}")
        # Проверяем, это команда или callback запрос
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                "❌ Произошла ошибка при проверке подписки. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard_for_user(update)
            )
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ Произошла ошибка при проверке подписки. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard_for_user(update)
            )

__all__.append('subscription_command')

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

__all__.append('handle_subscription_purchase')

async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает успешную оплату"""
    payment = update.message.successful_payment
    user = update.effective_user
    
    try:
        # Idempotency guard
        provider_charge_id = payment.provider_payment_charge_id if hasattr(payment, 'provider_payment_charge_id') else None
        if provider_charge_id and is_payment_processed(provider_charge_id):
            logger.info('Duplicate payment notification ignored')
            return
        
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
        
        if provider_charge_id:
            mark_payment_processed(provider_charge_id, user_id, stars_amount, payment.currency)
        
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

__all__.append('handle_successful_payment')

