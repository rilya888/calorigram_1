"""
Константы для бота Calorigram
"""

# Валидация данных
MIN_AGE = 1
MAX_AGE = 120
MIN_HEIGHT = 50
MAX_HEIGHT = 250
MIN_WEIGHT = 20
MAX_WEIGHT = 300

# Ограничения API
MAX_API_RETRIES = 3
API_TIMEOUT = 30
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB

# Сообщения
ERROR_MESSAGES = {
    'user_not_registered': "❌ Вы не зарегистрированы в системе!\nИспользуйте /register для регистрации.",
    'api_error': "❌ Ошибка API\n\nПопробуйте позже или обратитесь к администратору.",
    'validation_error': "❌ Ошибка валидации\n\nПроверьте введенные данные.",
    'database_error': "❌ Ошибка базы данных\n\nПопробуйте позже.",
    'file_too_large': "❌ Файл слишком большой\n\nМаксимальный размер: {}MB",
    'invalid_format': "❌ Неподдерживаемый формат файла",
    'processing_error': "❌ Ошибка обработки\n\nПопробуйте еще раз."
}

SUCCESS_MESSAGES = {
    'registration_complete': "✅ Регистрация завершена!",
    'data_deleted': "✅ Данные успешно удалены!",
    'analysis_complete': "✅ Анализ завершен!"
}

# Уровни активности
ACTIVITY_LEVELS = {
    'Минимальная': 1.2,
    'Легкая': 1.375,
    'Умеренная': 1.55,
    'Высокая': 1.725,
    'Очень высокая': 1.9
}

# Пол
GENDERS = ['Мужской', 'Женский']

# Цели пользователя
GOALS = {
    'lose_weight': 'Похудеть',
    'maintain': 'Держать себя в форме',
    'gain_weight': 'Набрать вес'
}

# Коэффициенты для расчета целевой нормы калорий
GOAL_MULTIPLIERS = {
    'lose_weight': 0.8,    # -20% от расчетной нормы
    'maintain': 1.0,       # Расчетная норма
    'gain_weight': 1.2     # +20% от расчетной нормы
}

# Callback data
CALLBACK_DATA = {
    'register': 'register',
    'help': 'help',
    'profile': 'profile',
    'menu': 'menu',
    'back_to_main': 'back_to_main',
    'add_dish': 'add_dish',
    'check_calories': 'check_calories',
    'addmeal': 'addmeal',
    'reset_confirm': 'reset_confirm',
    'analyze_photo': 'analyze_photo',
    'analyze_text': 'analyze_text',
    'analyze_voice': 'analyze_voice',
    'check_photo': 'check_photo',
    'check_text': 'check_text',
    'check_voice': 'check_voice',
    'statistics': 'statistics',
    'buy_subscription': 'buy_subscription',
    'payment_success': 'payment_success',
    'goal_lose_weight': 'goal_lose_weight',
    'goal_maintain': 'goal_maintain',
    'goal_gain_weight': 'goal_gain_weight'
}

# Команды бота
BOT_COMMANDS = [
    ('start', 'Начать работу с ботом'),
    ('register', 'Регистрация в системе'),
    ('profile', 'Посмотреть профиль'),
    ('add', 'Добавить блюдо'),
    ('analyze', '🤖 Универсальный анализ еды (автоопределение типа)'),
    ('addmeal', 'Анализ блюда (фото/текст/голос)'),
    ('addphoto', 'Анализ фото еды ИИ'),
    ('addtext', 'Анализ описания блюда ИИ'),
    ('addvoice', 'Анализ голосового описания ИИ'),
    ('reminders', 'Настройки напоминаний о приемах пищи'),
    ('terms', 'Условия подписки'),
    ('dayreset', 'Удалить данные за сегодня'),
    ('reset', 'Удалить все данные регистрации'),
    ('admin', 'Админ панель (только для админов)'),
    ('help', 'Показать справку')
]

# ID админов теперь настраивается через переменные окружения в config.py

# Цены подписок в Telegram Stars
SUBSCRIPTION_PRICES = {
    'trial': 0,  # Бесплатный триал
    'premium_7_days': 10  # 7 дней премиум за 10 звезд
}

# Описания подписок
SUBSCRIPTION_DESCRIPTIONS = {
    'trial': '🆓 Триальный период (1 день)',
    'premium_7_days': '💎 Премиум на 7 дней - 10 ⭐'
}

# Callback данные для админки
ADMIN_CALLBACKS = {
    'admin_panel': 'admin_panel',
    'admin_stats': 'admin_stats',
    'admin_users': 'admin_users',
    'admin_meals': 'admin_meals',
    'admin_broadcast': 'admin_broadcast',
    'admin_subscriptions': 'admin_subscriptions',
    'admin_check_subscription': 'admin_check_subscription',
    'admin_manage_subscription': 'admin_manage_subscription',
    'admin_activate_trial': 'admin_activate_trial',
    'admin_activate_premium': 'admin_activate_premium',
    'admin_deactivate_subscription': 'admin_deactivate_subscription',
    'admin_back': 'admin_back'
}
