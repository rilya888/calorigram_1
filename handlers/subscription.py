"""
Модуль для работы с подписками пользователей
"""
import logging
from typing import Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes

from database import (
    get_user_by_telegram_id,
    check_user_subscription,
    activate_premium_subscription,
    get_user_registration_history,
    create_user_registration_history,
    mark_trial_as_used
)
from constants import SUBSCRIPTION_PRICES, SUBSCRIPTION_DESCRIPTIONS
from config import BOT_TOKEN, TEST_MODE
from logging_config import get_logger

logger = get_logger(__name__)


# ==================== SUBSCRIPTION UTILITY FUNCTIONS ====================

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
            return "❌ **Триальный период истек**\n\nВаш бесплатный триальный период закончился. Для продолжения использования бота необходимо оформить подписку.\n\n🌟 **Оплата через Telegram Stars:**\n• 7 дней - 10 ⭐\n\n💎 Безопасно • Мгновенно • Без комиссий"
        elif access_info['subscription_type'] == 'trial_used':
            return "❌ **Триальный период уже был использован**\n\nВы уже использовали бесплатный триальный период. Для продолжения использования бота необходимо оформить подписку.\n\n🌟 **Оплата через Telegram Stars:**\n• 7 дней - 10 ⭐\n\n💎 Безопасно • Мгновенно • Без комиссий"
        else:
            return "❌ **Нет активной подписки**\n\nДля использования бота необходимо оформить подписку.\n\n🌟 **Оплата через Telegram Stars:**\n• 7 дней - 10 ⭐\n\n💎 Безопасно • Мгновенно • Без комиссий"
    
    return "Информация о подписке недоступна"


# ==================== COMMAND HANDLERS ====================

async def subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает информацию о подписке"""
    user = update.effective_user
    
    try:
        user_data = get_user_by_telegram_id(user.id)
        
        if not user_data:
            await update.message.reply_text(
                "❌ Вы не зарегистрированы!\n"
                "Используйте /register для регистрации."
            )
            return
        
        # Проверяем подписку
        subscription = check_user_subscription(user.id)
        
        if subscription['is_active']:
            # Показываем информацию об активной подписке
            message = f"""
⭐ **Ваша подписка**

Тип: {subscription['type']}
Статус: ✅ Активна
Действует до: {subscription['expires_at'] or 'Бессрочно'}

Спасибо за использование Calorigram!
            """
        else:
            # Показываем меню покупки подписки
            message = f"""
💎 **Оформление подписки**

{get_subscription_message(check_subscription_access(user.id))}

**Возможности с подпиской:**
✅ Неограниченный анализ блюд
✅ Детальная статистика
✅ Напоминания о приемах пищи
✅ Экспорт данных

🌟 Оплата через Telegram Stars - быстро и безопасно!
            """
        
        # Кнопки
        keyboard = []
        
        if not subscription['is_active']:
            # Проверяем, использовал ли пользователь триал
            history = get_user_registration_history(user.id)
            
            if not history or not history.get('trial_used', False):
                keyboard.append([InlineKeyboardButton("🆓 Попробовать бесплатно (3 дня)", callback_data="activate_trial")])
            
            keyboard.append([InlineKeyboardButton(f"⭐ Купить подписку (7 дней - {SUBSCRIPTION_PRICES['week']} Stars)", callback_data="purchase_week")])
        
        keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in subscription_command: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке информации о подписке")


# ==================== SUBSCRIPTION ACTIVATION ====================

async def activate_test_subscription(user_id: int, subscription_type: str, query: Any):
    """Активирует тестовую подписку (только в TEST_MODE)"""
    if not TEST_MODE:
        await query.edit_message_text(
            "❌ Тестовая подписка доступна только в режиме разработки"
        )
        return
    
    try:
        # Активируем премиум подписку
        days = 7 if subscription_type == 'week' else 30
        activate_premium_subscription(user_id, days=days)
        
        await query.edit_message_text(
            f"✅ **Тестовая подписка активирована!**\n\n"
            f"Тип: {subscription_type}\n"
            f"Срок: {days} дней\n\n"
            f"Это тестовая подписка для разработки."
        )
        
    except Exception as e:
        logger.error(f"Error activating test subscription: {e}")
        await query.edit_message_text("❌ Ошибка при активации тестовой подписки")


async def activate_trial_subscription(user_id: int, query: Any):
    """Активирует триальную подписку на 3 дня"""
    try:
        # Проверяем, не использовал ли пользователь триал ранее
        history = get_user_registration_history(user_id)
        
        if history and history.get('trial_used', False):
            await query.edit_message_text(
                "❌ **Триальный период уже был использован**\n\n"
                "Вы уже использовали бесплатный триальный период.\n"
                "Для продолжения необходимо оформить подписку."
            )
            return
        
        # Активируем триальную подписку на 3 дня
        activate_premium_subscription(user_id, days=3)
        
        # Отмечаем, что триал использован
        if not history:
            create_user_registration_history(user_id)
        mark_trial_as_used(user_id)
        
        await query.edit_message_text(
            "✅ **Триальный период активирован!**\n\n"
            "🆓 Вам доступны все функции бота на 3 дня\n\n"
            "После истечения триального периода вы сможете оформить подписку."
        )
        
    except Exception as e:
        logger.error(f"Error activating trial: {e}")
        await query.edit_message_text("❌ Ошибка при активации триального периода")


async def create_payment_invoice(user_id: int, subscription_type: str, price: int, query: Any, context: ContextTypes.DEFAULT_TYPE):
    """Создает инвойс для оплаты через Telegram Stars"""
    try:
        title = f"Подписка Calorigram ({subscription_type})"
        description = SUBSCRIPTION_DESCRIPTIONS.get(subscription_type, "Подписка на бота Calorigram")
        
        # Отправляем инвойс
        await context.bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=description,
            payload=f"subscription_{subscription_type}_{user_id}",
            provider_token="",  # Пустой для Telegram Stars
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label=title, amount=price)]
        )
        
        await query.edit_message_text(
            "💳 **Счет отправлен!**\n\n"
            "Проверьте сообщение выше для оплаты.\n\n"
            "После успешной оплаты подписка будет активирована автоматически."
        )
        
    except Exception as e:
        logger.error(f"Error creating payment invoice: {e}")
        await query.edit_message_text(
            "❌ Ошибка при создании счета для оплаты.\n"
            "Попробуйте позже."
        )


# ==================== CALLBACK HANDLERS ====================

async def handle_subscription_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик покупки подписки"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Определяем тип подписки
    if query.data == "purchase_week":
        subscription_type = "week"
        price = SUBSCRIPTION_PRICES['week']
    elif query.data == "purchase_month":
        subscription_type = "month"
        price = SUBSCRIPTION_PRICES.get('month', 30)
    else:
        await query.edit_message_text("❌ Неизвестный тип подписки")
        return
    
    # Создаем инвойс для оплаты
    await create_payment_invoice(user_id, subscription_type, price, query, context)


async def handle_activate_trial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик активации триального периода"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    await activate_trial_subscription(user_id, query)


async def handle_pre_checkout_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик pre-checkout запроса"""
    query = update.pre_checkout_query
    
    try:
        # Всегда подтверждаем pre-checkout
        await query.answer(ok=True)
        logger.info(f"Pre-checkout approved for user {query.from_user.id}, payload: {query.invoice_payload}")
        
    except Exception as e:
        logger.error(f"Error in pre-checkout: {e}")
        await query.answer(ok=False, error_message="Ошибка при проверке платежа")


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик успешной оплаты"""
    user_id = update.effective_user.id
    payment = update.message.successful_payment
    
    try:
        logger.info(f"Successful payment from user {user_id}: {payment.invoice_payload}")
        
        # Парсим payload для определения типа подписки
        payload_parts = payment.invoice_payload.split('_')
        
        if len(payload_parts) >= 2:
            subscription_type = payload_parts[1]
            
            # Определяем количество дней
            days = 7 if subscription_type == "week" else 30
            
            # Активируем подписку
            activate_premium_subscription(user_id, days=days)
            
            await update.message.reply_text(
                f"✅ **Оплата успешна!**\n\n"
                f"⭐ Премиум подписка активирована на {days} дней\n\n"
                f"Спасибо за поддержку! Теперь вам доступны все функции бота."
            )
        else:
            logger.error(f"Invalid payload format: {payment.invoice_payload}")
            await update.message.reply_text(
                "⚠️ Оплата получена, но возникла ошибка при активации подписки.\n"
                "Обратитесь в поддержку."
            )
            
    except Exception as e:
        logger.error(f"Error handling successful payment: {e}")
        await update.message.reply_text(
            "⚠️ Оплата получена, но возникла ошибка при активации подписки.\n"
            "Обратитесь в поддержку."
        )


async def show_subscription_purchase_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню покупки подписки"""
    query = update.callback_query if hasattr(update, 'callback_query') and update.callback_query else None
    user_id = update.effective_user.id
    
    try:
        # Проверяем, использовал ли пользователь триал
        history = get_user_registration_history(user_id)
        
        message = """
💎 **Оформление подписки Calorigram**

**Что вы получаете:**
✅ Неограниченный анализ блюд (фото, текст, голос)
✅ Детальная статистика калорий
✅ Напоминания о приемах пищи
✅ Персональные рекомендации
✅ Поддержка 24/7

🌟 **Оплата через Telegram Stars:**
• 7 дней - 10 ⭐

💎 Безопасно • Мгновенно • Без комиссий
        """
        
        keyboard = []
        
        # Добавляем кнопку триала, если не использовался
        if not history or not history.get('trial_used', False):
            keyboard.append([
                InlineKeyboardButton("🆓 Попробовать бесплатно (3 дня)", callback_data="activate_trial")
            ])
        
        keyboard.extend([
            [InlineKeyboardButton(f"⭐ 7 дней - {SUBSCRIPTION_PRICES['week']} Stars", callback_data="purchase_week")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error showing subscription menu: {e}")
        if query:
            await query.edit_message_text("❌ Ошибка при загрузке меню подписки")
        else:
            await update.message.reply_text("❌ Ошибка при загрузке меню подписки")

