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
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
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

# Часовые пояса для выбора при регистрации (группировка по полушариям)
TIMEZONE_HEMISPHERES = {
    'western': {
        'name': '🌍 Западное полушарие',
        'description': 'Америка, Тихий океан (UTC-12 до UTC+0)',
        'timezones': {
            'UTC-12': {
                'offset': -12,
                'name': 'UTC-12',
                'description': 'Бейкер, Хоуленд',
                'timezones': ['Pacific/Baker_Island', 'Pacific/Howland']
            },
            'UTC-11': {
                'offset': -11,
                'name': 'UTC-11',
                'description': 'Американское Самоа, Мидуэй',
                'timezones': ['Pacific/Pago_Pago', 'Pacific/Midway']
            },
            'UTC-10': {
                'offset': -10,
                'name': 'UTC-10',
                'description': 'Гавайи, Аляска (частично)',
                'timezones': ['Pacific/Honolulu', 'America/Adak']
            },
            'UTC-9': {
                'offset': -9,
                'name': 'UTC-9',
                'description': 'Аляска, Алеутские острова',
                'timezones': ['America/Anchorage', 'America/Adak']
            },
            'UTC-8': {
                'offset': -8,
                'name': 'UTC-8',
                'description': 'Лос-Анджелес, Ванкувер, Сиэтл',
                'timezones': ['America/Los_Angeles', 'America/Vancouver', 'America/Seattle']
            },
            'UTC-7': {
                'offset': -7,
                'name': 'UTC-7',
                'description': 'Денвер, Феникс, Калгари',
                'timezones': ['America/Denver', 'America/Phoenix', 'America/Calgary']
            },
            'UTC-6': {
                'offset': -6,
                'name': 'UTC-6',
                'description': 'Чикаго, Мехико, Мехико-Сити',
                'timezones': ['America/Chicago', 'America/Mexico_City', 'America/Winnipeg']
            },
            'UTC-5': {
                'offset': -5,
                'name': 'UTC-5',
                'description': 'Нью-Йорк, Торонто, Лима, Богота',
                'timezones': ['America/New_York', 'America/Toronto', 'America/Lima', 'America/Bogota']
            },
            'UTC-4': {
                'offset': -4,
                'name': 'UTC-4',
                'description': 'Сантьяго, Каракас, Ла-Пас',
                'timezones': ['America/Santiago', 'America/Caracas', 'America/La_Paz']
            },
            'UTC-3': {
                'offset': -3,
                'name': 'UTC-3',
                'description': 'Сан-Паулу, Буэнос-Айрес, Монтевидео',
                'timezones': ['America/Sao_Paulo', 'America/Buenos_Aires', 'America/Montevideo']
            },
            'UTC-2': {
                'offset': -2,
                'name': 'UTC-2',
                'description': 'Атлантический океан (острова)',
                'timezones': ['Atlantic/South_Georgia', 'Atlantic/Stanley']
            },
            'UTC-1': {
                'offset': -1,
                'name': 'UTC-1',
                'description': 'Азорские острова, Кабо-Верде',
                'timezones': ['Atlantic/Azores', 'Atlantic/Cape_Verde']
            },
            'UTC+0': {
                'offset': 0,
                'name': 'UTC+0',
                'description': 'Лондон, Дублин, Лиссабон',
                'timezones': ['Europe/London', 'Europe/Dublin', 'Europe/Lisbon']
            }
        }
    },
    'eastern': {
        'name': '🌏 Восточное полушарие',
        'description': 'Европа, Азия, Африка, Океания (UTC+1 до UTC+12)',
        'timezones': {
            'UTC+1': {
                'offset': 1,
                'name': 'UTC+1',
                'description': 'Париж, Берлин, Рим, Мадрид, Варшава',
                'timezones': ['Europe/Paris', 'Europe/Berlin', 'Europe/Rome', 'Europe/Madrid', 'Europe/Warsaw']
            },
            'UTC+2': {
                'offset': 2,
                'name': 'UTC+2',
                'description': 'Калининград, Киев, Хельсинки, Афины',
                'timezones': ['Europe/Kaliningrad', 'Europe/Kiev', 'Europe/Helsinki', 'Europe/Athens']
            },
            'UTC+3': {
                'offset': 3,
                'name': 'UTC+3',
                'description': 'Москва, Минск, Стамбул, Эр-Рияд',
                'timezones': ['Europe/Moscow', 'Europe/Minsk', 'Europe/Istanbul', 'Asia/Riyadh']
            },
            'UTC+4': {
                'offset': 4,
                'name': 'UTC+4',
                'description': 'Самара, Тбилиси, Ереван, Баку, Дубай',
                'timezones': ['Europe/Samara', 'Asia/Tbilisi', 'Asia/Yerevan', 'Asia/Baku', 'Asia/Dubai']
            },
            'UTC+5': {
                'offset': 5,
                'name': 'UTC+5',
                'description': 'Екатеринбург, Ташкент, Душанбе, Карачи',
                'timezones': ['Asia/Yekaterinburg', 'Asia/Tashkent', 'Asia/Dushanbe', 'Asia/Karachi']
            },
            'UTC+6': {
                'offset': 6,
                'name': 'UTC+6',
                'description': 'Омск, Алматы, Бишкек, Дакка',
                'timezones': ['Asia/Omsk', 'Asia/Almaty', 'Asia/Bishkek', 'Asia/Dhaka']
            },
            'UTC+7': {
                'offset': 7,
                'name': 'UTC+7',
                'description': 'Новосибирск, Красноярск, Бангкок, Джакарта',
                'timezones': ['Asia/Novosibirsk', 'Asia/Krasnoyarsk', 'Asia/Bangkok', 'Asia/Jakarta']
            },
            'UTC+8': {
                'offset': 8,
                'name': 'UTC+8',
                'description': 'Иркутск, Шанхай, Сингапур, Гонконг, Перт',
                'timezones': ['Asia/Irkutsk', 'Asia/Shanghai', 'Asia/Singapore', 'Asia/Hong_Kong', 'Australia/Perth']
            },
            'UTC+9': {
                'offset': 9,
                'name': 'UTC+9',
                'description': 'Якутск, Токио, Сеул, Куала-Лумпур',
                'timezones': ['Asia/Yakutsk', 'Asia/Tokyo', 'Asia/Seoul', 'Asia/Kuala_Lumpur']
            },
            'UTC+10': {
                'offset': 10,
                'name': 'UTC+10',
                'description': 'Владивосток, Сидней, Мельбурн, Брисбен',
                'timezones': ['Asia/Vladivostok', 'Australia/Sydney', 'Australia/Melbourne', 'Australia/Brisbane']
            },
            'UTC+11': {
                'offset': 11,
                'name': 'UTC+11',
                'description': 'Магадан, Новая Каледония, Соломоновы острова',
                'timezones': ['Asia/Magadan', 'Pacific/Noumea', 'Pacific/Guadalcanal']
            },
            'UTC+12': {
                'offset': 12,
                'name': 'UTC+12',
                'description': 'Камчатка, Окленд, Фиджи, Новая Зеландия',
                'timezones': ['Asia/Kamchatka', 'Pacific/Auckland', 'Pacific/Fiji']
            }
        }
    }
}

# Старые часовые пояса для обратной совместимости (группировка по UTC смещению)
TIMEZONE_GROUPS = {
    'UTC-12': {
        'offset': -12,
        'name': 'UTC-12',
        'description': 'Бейкер, Хоуленд',
        'timezones': ['Pacific/Baker_Island', 'Pacific/Howland']
    },
    'UTC-11': {
        'offset': -11,
        'name': 'UTC-11',
        'description': 'Американское Самоа, Мидуэй',
        'timezones': ['Pacific/Pago_Pago', 'Pacific/Midway']
    },
    'UTC-10': {
        'offset': -10,
        'name': 'UTC-10',
        'description': 'Гавайи, Аляска (частично)',
        'timezones': ['Pacific/Honolulu', 'America/Adak']
    },
    'UTC-9': {
        'offset': -9,
        'name': 'UTC-9',
        'description': 'Аляска, Алеутские острова',
        'timezones': ['America/Anchorage', 'America/Adak']
    },
    'UTC-8': {
        'offset': -8,
        'name': 'UTC-8',
        'description': 'Лос-Анджелес, Ванкувер, Сиэтл',
        'timezones': ['America/Los_Angeles', 'America/Vancouver', 'America/Seattle']
    },
    'UTC-7': {
        'offset': -7,
        'name': 'UTC-7',
        'description': 'Денвер, Феникс, Калгари',
        'timezones': ['America/Denver', 'America/Phoenix', 'America/Calgary']
    },
    'UTC-6': {
        'offset': -6,
        'name': 'UTC-6',
        'description': 'Чикаго, Мехико, Мехико-Сити',
        'timezones': ['America/Chicago', 'America/Mexico_City', 'America/Winnipeg']
    },
    'UTC-5': {
        'offset': -5,
        'name': 'UTC-5',
        'description': 'Нью-Йорк, Торонто, Лима, Богота',
        'timezones': ['America/New_York', 'America/Toronto', 'America/Lima', 'America/Bogota']
    },
    'UTC-4': {
        'offset': -4,
        'name': 'UTC-4',
        'description': 'Сантьяго, Каракас, Ла-Пас',
        'timezones': ['America/Santiago', 'America/Caracas', 'America/La_Paz']
    },
    'UTC-3': {
        'offset': -3,
        'name': 'UTC-3',
        'description': 'Сан-Паулу, Буэнос-Айрес, Монтевидео',
        'timezones': ['America/Sao_Paulo', 'America/Buenos_Aires', 'America/Montevideo']
    },
    'UTC-2': {
        'offset': -2,
        'name': 'UTC-2',
        'description': 'Атлантический океан (острова)',
        'timezones': ['Atlantic/South_Georgia', 'Atlantic/Stanley']
    },
    'UTC-1': {
        'offset': -1,
        'name': 'UTC-1',
        'description': 'Азорские острова, Кабо-Верде',
        'timezones': ['Atlantic/Azores', 'Atlantic/Cape_Verde']
    },
    'UTC+0': {
        'offset': 0,
        'name': 'UTC+0',
        'description': 'Лондон, Дублин, Лиссабон',
        'timezones': ['Europe/London', 'Europe/Dublin', 'Europe/Lisbon']
    },
    'UTC+1': {
        'offset': 1,
        'name': 'UTC+1',
        'description': 'Париж, Берлин, Рим, Мадрид, Варшава',
        'timezones': ['Europe/Paris', 'Europe/Berlin', 'Europe/Rome', 'Europe/Madrid', 'Europe/Warsaw']
    },
    'UTC+2': {
        'offset': 2,
        'name': 'UTC+2',
        'description': 'Калининград, Киев, Хельсинки, Афины',
        'timezones': ['Europe/Kaliningrad', 'Europe/Kiev', 'Europe/Helsinki', 'Europe/Athens']
    },
    'UTC+3': {
        'offset': 3,
        'name': 'UTC+3',
        'description': 'Москва, Минск, Стамбул, Эр-Рияд',
        'timezones': ['Europe/Moscow', 'Europe/Minsk', 'Europe/Istanbul', 'Asia/Riyadh']
    },
    'UTC+4': {
        'offset': 4,
        'name': 'UTC+4',
        'description': 'Самара, Тбилиси, Ереван, Баку, Дубай',
        'timezones': ['Europe/Samara', 'Asia/Tbilisi', 'Asia/Yerevan', 'Asia/Baku', 'Asia/Dubai']
    },
    'UTC+5': {
        'offset': 5,
        'name': 'UTC+5',
        'description': 'Екатеринбург, Ташкент, Душанбе, Карачи',
        'timezones': ['Asia/Yekaterinburg', 'Asia/Tashkent', 'Asia/Dushanbe', 'Asia/Karachi']
    },
    'UTC+6': {
        'offset': 6,
        'name': 'UTC+6',
        'description': 'Омск, Алматы, Бишкек, Дакка',
        'timezones': ['Asia/Omsk', 'Asia/Almaty', 'Asia/Bishkek', 'Asia/Dhaka']
    },
    'UTC+7': {
        'offset': 7,
        'name': 'UTC+7',
        'description': 'Новосибирск, Красноярск, Бангкок, Джакарта',
        'timezones': ['Asia/Novosibirsk', 'Asia/Krasnoyarsk', 'Asia/Bangkok', 'Asia/Jakarta']
    },
    'UTC+8': {
        'offset': 8,
        'name': 'UTC+8',
        'description': 'Иркутск, Шанхай, Сингапур, Гонконг, Перт',
        'timezones': ['Asia/Irkutsk', 'Asia/Shanghai', 'Asia/Singapore', 'Asia/Hong_Kong', 'Australia/Perth']
    },
    'UTC+9': {
        'offset': 9,
        'name': 'UTC+9',
        'description': 'Якутск, Токио, Сеул, Куала-Лумпур',
        'timezones': ['Asia/Yakutsk', 'Asia/Tokyo', 'Asia/Seoul', 'Asia/Kuala_Lumpur']
    },
    'UTC+10': {
        'offset': 10,
        'name': 'UTC+10',
        'description': 'Владивосток, Сидней, Мельбурн, Брисбен',
        'timezones': ['Asia/Vladivostok', 'Australia/Sydney', 'Australia/Melbourne', 'Australia/Brisbane']
    },
    'UTC+11': {
        'offset': 11,
        'name': 'UTC+11',
        'description': 'Магадан, Новая Каледония, Соломоновы острова',
        'timezones': ['Asia/Magadan', 'Pacific/Noumea', 'Pacific/Guadalcanal']
    },
    'UTC+12': {
        'offset': 12,
        'name': 'UTC+12',
        'description': 'Камчатка, Окленд, Фиджи, Новая Зеландия',
        'timezones': ['Asia/Kamchatka', 'Pacific/Auckland', 'Pacific/Fiji']
    }
}

# Старые часовые пояса для обратной совместимости
TIMEZONES = {
    # Россия (11 часовых поясов)
    'Europe/Kaliningrad': '🇷🇺 Калининград (UTC+2)',
    'Europe/Moscow': '🇷🇺 Москва (UTC+3)',
    'Europe/Samara': '🇷🇺 Самара (UTC+4)',
    'Asia/Yekaterinburg': '🇷🇺 Екатеринбург (UTC+5)',
    'Asia/Omsk': '🇷🇺 Омск (UTC+6)',
    'Asia/Novosibirsk': '🇷🇺 Новосибирск (UTC+7)',
    'Asia/Krasnoyarsk': '🇷🇺 Красноярск (UTC+7)',
    'Asia/Irkutsk': '🇷🇺 Иркутск (UTC+8)',
    'Asia/Yakutsk': '🇷🇺 Якутск (UTC+9)',
    'Asia/Vladivostok': '🇷🇺 Владивосток (UTC+10)',
    'Asia/Magadan': '🇷🇺 Магадан (UTC+11)',
    'Asia/Kamchatka': '🇷🇺 Камчатка (UTC+12)',
    
    # СНГ
    'Europe/Minsk': '🇧🇾 Минск (UTC+3)',
    'Europe/Kiev': '🇺🇦 Киев (UTC+2)',
    'Asia/Almaty': '🇰🇿 Алматы (UTC+6)',
    'Asia/Tashkent': '🇺🇿 Ташкент (UTC+5)',
    'Asia/Tbilisi': '🇬🇪 Тбилиси (UTC+4)',
    'Asia/Yerevan': '🇦🇲 Ереван (UTC+4)',
    'Asia/Baku': '🇦🇿 Баку (UTC+4)',
    'Asia/Bishkek': '🇰🇬 Бишкек (UTC+6)',
    'Asia/Dushanbe': '🇹🇯 Душанбе (UTC+5)',
    
    # Европа
    'Europe/London': '🇬🇧 Лондон (UTC+0)',
    'Europe/Paris': '🇫🇷 Париж (UTC+1)',
    'Europe/Berlin': '🇩🇪 Берлин (UTC+1)',
    'Europe/Rome': '🇮🇹 Рим (UTC+1)',
    'Europe/Madrid': '🇪🇸 Мадрид (UTC+1)',
    'Europe/Warsaw': '🇵🇱 Варшава (UTC+1)',
    'Europe/Prague': '🇨🇿 Прага (UTC+1)',
    'Europe/Vienna': '🇦🇹 Вена (UTC+1)',
    'Europe/Brussels': '🇧🇪 Брюссель (UTC+1)',
    'Europe/Amsterdam': '🇳🇱 Амстердам (UTC+1)',
    'Europe/Stockholm': '🇸🇪 Стокгольм (UTC+1)',
    'Europe/Oslo': '🇳🇴 Осло (UTC+1)',
    'Europe/Copenhagen': '🇩🇰 Копенгаген (UTC+1)',
    'Europe/Helsinki': '🇫🇮 Хельсинки (UTC+2)',
    'Europe/Athens': '🇬🇷 Афины (UTC+2)',
    'Europe/Bucharest': '🇷🇴 Бухарест (UTC+2)',
    'Europe/Sofia': '🇧🇬 София (UTC+2)',
    'Europe/Istanbul': '🇹🇷 Стамбул (UTC+3)',
    'Europe/Lisbon': '🇵🇹 Лиссабон (UTC+0)',
    'Europe/Dublin': '🇮🇪 Дублин (UTC+0)',
    
    # Азия
    'Asia/Dubai': '🇦🇪 Дубай (UTC+4)',
    'Asia/Shanghai': '🇨🇳 Шанхай (UTC+8)',
    'Asia/Tokyo': '🇯🇵 Токио (UTC+9)',
    'Asia/Seoul': '🇰🇷 Сеул (UTC+9)',
    'Asia/Bangkok': '🇹🇭 Бангкок (UTC+7)',
    'Asia/Singapore': '🇸🇬 Сингапур (UTC+8)',
    'Asia/Hong_Kong': '🇭🇰 Гонконг (UTC+8)',
    'Asia/Kuala_Lumpur': '🇲🇾 Куала-Лумпур (UTC+8)',
    'Asia/Jakarta': '🇮🇩 Джакарта (UTC+7)',
    'Asia/Manila': '🇵🇭 Манила (UTC+8)',
    'Asia/Kolkata': '🇮🇳 Дели (UTC+5:30)',
    'Asia/Karachi': '🇵🇰 Карачи (UTC+5)',
    'Asia/Dhaka': '🇧🇩 Дакка (UTC+6)',
    'Asia/Kathmandu': '🇳🇵 Катманду (UTC+5:45)',
    'Asia/Tehran': '🇮🇷 Тегеран (UTC+3:30)',
    'Asia/Jerusalem': '🇮🇱 Иерусалим (UTC+2)',
    'Asia/Riyadh': '🇸🇦 Эр-Рияд (UTC+3)',
    
    # Америка
    'America/New_York': '🇺🇸 Нью-Йорк (UTC-5)',
    'America/Chicago': '🇺🇸 Чикаго (UTC-6)',
    'America/Denver': '🇺🇸 Денвер (UTC-7)',
    'America/Los_Angeles': '🇺🇸 Лос-Анджелес (UTC-8)',
    'America/Anchorage': '🇺🇸 Анкоридж (UTC-9)',
    'America/Toronto': '🇨🇦 Торонто (UTC-5)',
    'America/Vancouver': '🇨🇦 Ванкувер (UTC-8)',
    'America/Mexico_City': '🇲🇽 Мехико (UTC-6)',
    'America/Sao_Paulo': '🇧🇷 Сан-Паулу (UTC-3)',
    'America/Buenos_Aires': '🇦🇷 Буэнос-Айрес (UTC-3)',
    'America/Lima': '🇵🇪 Лима (UTC-5)',
    'America/Bogota': '🇨🇴 Богота (UTC-5)',
    'America/Santiago': '🇨🇱 Сантьяго (UTC-4)',
    
    # Австралия и Океания
    'Australia/Sydney': '🇦🇺 Сидней (UTC+10)',
    'Australia/Melbourne': '🇦🇺 Мельбурн (UTC+10)',
    'Australia/Brisbane': '🇦🇺 Брисбен (UTC+10)',
    'Australia/Perth': '🇦🇺 Перт (UTC+8)',
    'Pacific/Auckland': '🇳🇿 Окленд (UTC+12)',
    
    # Африка
    'Africa/Cairo': '🇪🇬 Каир (UTC+2)',
    'Africa/Johannesburg': '🇿🇦 Йоханнесбург (UTC+2)',
    'Africa/Lagos': '🇳🇬 Лагос (UTC+1)',
    'Africa/Nairobi': '🇰🇪 Найроби (UTC+3)',
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
    'goal_gain_weight': 'goal_gain_weight',
    # Новые callback для подтверждения анализа фото
    'confirm_analysis': 'confirm_analysis',
    'add_to_analysis': 'add_to_analysis',
    'confirm_check_analysis': 'confirm_check_analysis',
    'add_to_check_analysis': 'add_to_check_analysis',
    'cancel_analysis': 'cancel_analysis'
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
