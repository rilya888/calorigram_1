"""
Команды для управления напоминаниями о приемах пищи
"""
from logging_config import get_logger
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import (
    get_user_reminder_settings, 
    update_user_timezone, 
    update_user_reminders,
    get_user_by_telegram_id
)
from reminder_sender import send_test_reminder

logger = get_logger(__name__)

# Список всех часовых поясов (синхронизирован с регистрацией)
TIMEZONES = [
    # Россия (11 часовых поясов)
    ("Europe/Kaliningrad", "🇷🇺 Калининград (UTC+2)"),
    ("Europe/Moscow", "🇷🇺 Москва (UTC+3)"),
    ("Europe/Samara", "🇷🇺 Самара (UTC+4)"),
    ("Asia/Yekaterinburg", "🇷🇺 Екатеринбург (UTC+5)"),
    ("Asia/Omsk", "🇷🇺 Омск (UTC+6)"),
    ("Asia/Novosibirsk", "🇷🇺 Новосибирск (UTC+7)"),
    ("Asia/Krasnoyarsk", "🇷🇺 Красноярск (UTC+7)"),
    ("Asia/Irkutsk", "🇷🇺 Иркутск (UTC+8)"),
    ("Asia/Yakutsk", "🇷🇺 Якутск (UTC+9)"),
    ("Asia/Vladivostok", "🇷🇺 Владивосток (UTC+10)"),
    ("Asia/Magadan", "🇷🇺 Магадан (UTC+11)"),
    ("Asia/Kamchatka", "🇷🇺 Камчатка (UTC+12)"),
    
    # СНГ
    ("Europe/Minsk", "🇧🇾 Минск (UTC+3)"),
    ("Europe/Kiev", "🇺🇦 Киев (UTC+2)"),
    ("Asia/Almaty", "🇰🇿 Алматы (UTC+6)"),
    ("Asia/Tashkent", "🇺🇿 Ташкент (UTC+5)"),
    ("Asia/Tbilisi", "🇬🇪 Тбилиси (UTC+4)"),
    ("Asia/Yerevan", "🇦🇲 Ереван (UTC+4)"),
    ("Asia/Baku", "🇦🇿 Баку (UTC+4)"),
    ("Asia/Bishkek", "🇰🇬 Бишкек (UTC+6)"),
    ("Asia/Dushanbe", "🇹🇯 Душанбе (UTC+5)"),
    
    # Европа
    ("Europe/London", "🇬🇧 Лондон (UTC+0)"),
    ("Europe/Paris", "🇫🇷 Париж (UTC+1)"),
    ("Europe/Berlin", "🇩🇪 Берлин (UTC+1)"),
    ("Europe/Rome", "🇮🇹 Рим (UTC+1)"),
    ("Europe/Madrid", "🇪🇸 Мадрид (UTC+1)"),
    ("Europe/Warsaw", "🇵🇱 Варшава (UTC+1)"),
    ("Europe/Prague", "🇨🇿 Прага (UTC+1)"),
    ("Europe/Vienna", "🇦🇹 Вена (UTC+1)"),
    ("Europe/Brussels", "🇧🇪 Брюссель (UTC+1)"),
    ("Europe/Amsterdam", "🇳🇱 Амстердам (UTC+1)"),
    ("Europe/Stockholm", "🇸🇪 Стокгольм (UTC+1)"),
    ("Europe/Oslo", "🇳🇴 Осло (UTC+1)"),
    ("Europe/Copenhagen", "🇩🇰 Копенгаген (UTC+1)"),
    ("Europe/Helsinki", "🇫🇮 Хельсинки (UTC+2)"),
    ("Europe/Athens", "🇬🇷 Афины (UTC+2)"),
    ("Europe/Bucharest", "🇷🇴 Бухарест (UTC+2)"),
    ("Europe/Sofia", "🇧🇬 София (UTC+2)"),
    ("Europe/Istanbul", "🇹🇷 Стамбул (UTC+3)"),
    ("Europe/Lisbon", "🇵🇹 Лиссабон (UTC+0)"),
    ("Europe/Dublin", "🇮🇪 Дублин (UTC+0)"),
    
    # Азия
    ("Asia/Dubai", "🇦🇪 Дубай (UTC+4)"),
    ("Asia/Shanghai", "🇨🇳 Шанхай (UTC+8)"),
    ("Asia/Tokyo", "🇯🇵 Токио (UTC+9)"),
    ("Asia/Seoul", "🇰🇷 Сеул (UTC+9)"),
    ("Asia/Bangkok", "🇹🇭 Бангкок (UTC+7)"),
    ("Asia/Singapore", "🇸🇬 Сингапур (UTC+8)"),
    ("Asia/Hong_Kong", "🇭🇰 Гонконг (UTC+8)"),
    ("Asia/Kuala_Lumpur", "🇲🇾 Куала-Лумпур (UTC+8)"),
    ("Asia/Jakarta", "🇮🇩 Джакарта (UTC+7)"),
    ("Asia/Manila", "🇵🇭 Манила (UTC+8)"),
    ("Asia/Kolkata", "🇮🇳 Дели (UTC+5:30)"),
    ("Asia/Karachi", "🇵🇰 Карачи (UTC+5)"),
    ("Asia/Dhaka", "🇧🇩 Дакка (UTC+6)"),
    ("Asia/Kathmandu", "🇳🇵 Катманду (UTC+5:45)"),
    ("Asia/Tehran", "🇮🇷 Тегеран (UTC+3:30)"),
    ("Asia/Jerusalem", "🇮🇱 Иерусалим (UTC+2)"),
    ("Asia/Riyadh", "🇸🇦 Эр-Рияд (UTC+3)"),
    
    # Америка
    ("America/New_York", "🇺🇸 Нью-Йорк (UTC-5)"),
    ("America/Chicago", "🇺🇸 Чикаго (UTC-6)"),
    ("America/Denver", "🇺🇸 Денвер (UTC-7)"),
    ("America/Los_Angeles", "🇺🇸 Лос-Анджелес (UTC-8)"),
    ("America/Anchorage", "🇺🇸 Анкоридж (UTC-9)"),
    ("America/Toronto", "🇨🇦 Торонто (UTC-5)"),
    ("America/Vancouver", "🇨🇦 Ванкувер (UTC-8)"),
    ("America/Mexico_City", "🇲🇽 Мехико (UTC-6)"),
    ("America/Sao_Paulo", "🇧🇷 Сан-Паулу (UTC-3)"),
    ("America/Buenos_Aires", "🇦🇷 Буэнос-Айрес (UTC-3)"),
    ("America/Lima", "🇵🇪 Лима (UTC-5)"),
    ("America/Bogota", "🇨🇴 Богота (UTC-5)"),
    ("America/Santiago", "🇨🇱 Сантьяго (UTC-4)"),
    ("America/Caracas", "🇻🇪 Каракас (UTC-4)"),
    ("Atlantic/South_Georgia", "🇬🇸 Южная Георгия (UTC-2)"),
    ("Atlantic/Azores", "🇵🇹 Азорские острова (UTC-1)"),
    ("Pacific/Honolulu", "🇺🇸 Гонолулу (UTC-10)"),
    ("Pacific/Baker_Island", "🇺🇸 Бейкер (UTC-12)"),
    
    # Австралия и Океания
    ("Australia/Sydney", "🇦🇺 Сидней (UTC+10)"),
    ("Australia/Melbourne", "🇦🇺 Мельбурн (UTC+10)"),
    ("Australia/Brisbane", "🇦🇺 Брисбен (UTC+10)"),
    ("Australia/Perth", "🇦🇺 Перт (UTC+8)"),
    ("Australia/Adelaide", "🇦🇺 Аделаида (UTC+9:30)"),
    ("Pacific/Auckland", "🇳🇿 Окленд (UTC+12)"),
    ("Pacific/Fiji", "🇫🇯 Фиджи (UTC+12)"),
    ("Pacific/Noumea", "🇳🇨 Нумеа (UTC+11)"),
    
    # Африка
    ("Africa/Cairo", "🇪🇬 Каир (UTC+2)"),
    ("Africa/Johannesburg", "🇿🇦 Йоханнесбург (UTC+2)"),
    ("Africa/Lagos", "🇳🇬 Лагос (UTC+1)"),
    ("Africa/Nairobi", "🇰🇪 Найроби (UTC+3)"),
]

async def reminder_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда настроек напоминаний"""
    user = update.effective_user
    
    # Получаем текущие настройки
    settings = get_user_reminder_settings(user.id)
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("🕘 Изменить часовой пояс", callback_data="reminder_timezone")],
        [InlineKeyboardButton("🔔 Включить напоминания", callback_data="reminder_enable") if not settings['reminders_enabled'] 
         else InlineKeyboardButton("🔕 Отключить напоминания", callback_data="reminder_disable")],
        [InlineKeyboardButton("📋 Текущие настройки", callback_data="reminder_info")],
        [InlineKeyboardButton("🧪 Тестовое напоминание", callback_data="reminder_test")],
        [InlineKeyboardButton("🔙 Назад", callback_data="profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status = "✅ Включены" if settings['reminders_enabled'] else "❌ Отключены"
    
    message = f"""
🔔 **Настройки напоминаний**

**Текущий статус:** {status}
**Часовой пояс:** {settings['timezone']}

**Время напоминаний:**
• 🌅 9:00 - Завтрак
• ☀️ 14:00 - Обед  
• 🌙 19:00 - Ужин

Выберите действие:
"""
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов для настроек напоминаний"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    data = query.data
    
    if data == "reminder_settings":
        await show_reminder_settings(query, context)
    elif data == "reminder_timezone":
        await show_timezone_selection(query, context)
    elif data == "reminder_enable":
        await enable_reminders(query, context)
    elif data == "reminder_disable":
        await disable_reminders(query, context)
    elif data == "reminder_info":
        await show_reminder_info(query, context)
    elif data == "reminder_test":
        await send_test_reminder_callback(query, context)
    elif data.startswith("timezone_"):
        timezone = data.replace("timezone_", "").replace("_", "/")
        await set_timezone(query, context, timezone)

async def show_reminder_settings(query, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню настроек напоминаний"""
    user = query.from_user
    
    # Получаем текущие настройки
    settings = get_user_reminder_settings(user.id)
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("🕘 Изменить часовой пояс", callback_data="reminder_timezone")],
        [InlineKeyboardButton("🔔 Включить напоминания", callback_data="reminder_enable") if not settings['reminders_enabled'] 
         else InlineKeyboardButton("🔕 Отключить напоминания", callback_data="reminder_disable")],
        [InlineKeyboardButton("📋 Текущие настройки", callback_data="reminder_info")],
        [InlineKeyboardButton("🧪 Тестовое напоминание", callback_data="reminder_test")],
        [InlineKeyboardButton("🔙 Назад", callback_data="profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status = "✅ Включены" if settings['reminders_enabled'] else "❌ Отключены"
    
    message = f"""
🔔 **Настройки напоминаний**

**Текущий статус:** {status}
**Часовой пояс:** {settings['timezone']}

**Время напоминаний:**
• 🌅 9:00 - Завтрак
• ☀️ 14:00 - Обед  
• 🌙 19:00 - Ужин

Выберите действие:
"""
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_timezone_selection(query, context: ContextTypes.DEFAULT_TYPE):
    """Показывает выбор часового пояса"""
    keyboard = []
    
    # Создаем кнопки для выбора часового пояса (по 1 в ряду для лучшей читаемости)
    for timezone, name in TIMEZONES:
        callback_data = f"timezone_{timezone.replace('/', '_')}"
        keyboard.append([InlineKeyboardButton(name, callback_data=callback_data)])
    
    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="reminder_settings")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = """
🌍 **Выберите часовой пояс**

Напоминания будут приходить в соответствии с вашим местным временем.

📋 **Доступно 94 часовых пояса** (все регионы мира)

Выберите ваш часовой пояс:
"""
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def set_timezone(query, context: ContextTypes.DEFAULT_TYPE, timezone: str):
    """Устанавливает часовой пояс пользователя"""
    try:
        user = query.from_user
        
        if not timezone or not isinstance(timezone, str):
            await query.edit_message_text(
                "❌ Неверный часовой пояс. Попробуйте еще раз.",
                parse_mode='Markdown'
            )
            return
            
        if update_user_timezone(user.id, timezone):
            # Находим название часового пояса
            timezone_name = next((name for tz, name in TIMEZONES if tz == timezone), timezone)
            
            await query.edit_message_text(
                f"✅ Часовой пояс изменен на {timezone_name}\n\n"
                f"Напоминания теперь будут приходить по времени: {timezone}",
                parse_mode='Markdown'
            )
            
            logger.info(f"User {user.id} changed timezone to {timezone}")
        else:
            await query.edit_message_text(
                "❌ Ошибка при изменении часового пояса. Попробуйте позже.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error setting timezone: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            parse_mode='Markdown'
        )

async def enable_reminders(query, context: ContextTypes.DEFAULT_TYPE):
    """Включает напоминания"""
    user = query.from_user
    
    if update_user_reminders(user.id, True):
        await query.edit_message_text(
            "✅ Напоминания включены!\n\n"
            "Вы будете получать напоминания о приемах пищи в:\n"
            "• 🌅 9:00 - Завтрак\n"
            "• ☀️ 14:00 - Обед\n"
            "• 🌙 19:00 - Ужин",
            parse_mode='Markdown'
        )
        
        logger.info(f"User {user.id} enabled reminders")
    else:
        await query.edit_message_text(
            "❌ Ошибка при включении напоминаний. Попробуйте позже.",
            parse_mode='Markdown'
        )

async def disable_reminders(query, context: ContextTypes.DEFAULT_TYPE):
    """Отключает напоминания"""
    user = query.from_user
    
    if update_user_reminders(user.id, False):
        await query.edit_message_text(
            "🔕 Напоминания отключены!\n\n"
            "Вы больше не будете получать автоматические напоминания о приемах пищи.\n\n"
            "Чтобы включить их снова, используйте команду /reminders",
            parse_mode='Markdown'
        )
        
        logger.info(f"User {user.id} disabled reminders")
    else:
        await query.edit_message_text(
            "❌ Ошибка при отключении напоминаний. Попробуйте позже.",
            parse_mode='Markdown'
        )

async def show_reminder_info(query, context: ContextTypes.DEFAULT_TYPE):
    """Показывает информацию о текущих настройках напоминаний"""
    user = query.from_user
    settings = get_user_reminder_settings(user.id)
    
    # Получаем информацию о пользователе
    user_data = get_user_by_telegram_id(user.id)
    if not user_data:
        await query.edit_message_text(
            "❌ Пользователь не найден. Сначала зарегистрируйтесь командой /register",
            parse_mode='Markdown'
        )
        return
    
    status = "✅ Включены" if settings['reminders_enabled'] else "❌ Отключены"
    
    # Находим название часового пояса
    timezone_name = next((name for tz, name in TIMEZONES if tz == settings['timezone']), settings['timezone'])
    
    message = f"""
📋 **Текущие настройки напоминаний**

👤 **Пользователь:** {user_data[2]} (ID: {user.id})
🔔 **Статус:** {status}
🌍 **Часовой пояс:** {timezone_name}

⏰ **Время напоминаний:**
• 🌅 9:00 - Завтрак
• ☀️ 14:00 - Обед
• 🌙 19:00 - Ужин

💡 **Как это работает:**
Напоминания приходят только если вы еще не добавили прием пищи в этот день. Если вы уже добавили завтрак в 8:30, напоминание в 9:00 не придет.

🔧 **Управление:**
Используйте кнопки ниже для изменения настроек.
"""
    
    keyboard = [
        [InlineKeyboardButton("🕘 Изменить часовой пояс", callback_data="reminder_timezone")],
        [InlineKeyboardButton("🔔 Включить напоминания", callback_data="reminder_enable") if not settings['reminders_enabled'] 
         else InlineKeyboardButton("🔕 Отключить напоминания", callback_data="reminder_disable")],
        [InlineKeyboardButton("🔙 Назад", callback_data="reminder_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def send_test_reminder_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет тестовое напоминание пользователю"""
    user = query.from_user
    
    try:
        # Показываем сообщение о начале отправки
        await query.edit_message_text(
            "🧪 **Отправляю тестовое напоминание...**\n\n"
            "Пожалуйста, подождите...",
            parse_mode='Markdown'
        )
        
        # Отправляем тестовое напоминание
        success = await send_test_reminder(user.id)
        
        if success:
            await query.edit_message_text(
                "✅ **Тестовое напоминание отправлено!**\n\n"
                "Проверьте, получили ли вы сообщение с тестовым напоминанием.\n\n"
                "Если вы получили сообщение, значит напоминания работают корректно!",
                parse_mode='Markdown'
            )
            logger.info(f"Test reminder sent successfully to user {user.id}")
        else:
            await query.edit_message_text(
                "❌ **Ошибка отправки тестового напоминания**\n\n"
                "Возможные причины:\n"
                "• Проблемы с подключением к Telegram\n"
                "• Бот заблокирован пользователем\n"
                "• Временные технические проблемы\n\n"
                "Попробуйте позже или обратитесь к администратору.",
                parse_mode='Markdown'
            )
            logger.error(f"Failed to send test reminder to user {user.id}")
            
    except Exception as e:
        logger.error(f"Error in send_test_reminder_callback: {e}")
        await query.edit_message_text(
            "❌ **Произошла ошибка**\n\n"
            "Не удалось отправить тестовое напоминание. Попробуйте позже.",
            parse_mode='Markdown'
        )
