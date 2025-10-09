# 🏗️ Структура проекта Calorigram

## 📂 Основная структура

```
/Users/mac/
├── add_meal_multi/          # 🤖 Основной проект (рабочий бот)
│   ├── handlers/            # Обработчики команд Telegram
│   │   ├── __init__.py
│   │   ├── _shared.py       # Общие функции
│   │   ├── admin.py         # Админ панель
│   │   ├── commands_start.py # Команда /start
│   │   ├── media.py         # Обработка фото/голоса
│   │   ├── menu.py          # Главное меню
│   │   ├── misc.py          # Разные обработчики (основные функции)
│   │   ├── payments.py      # Платежи
│   │   ├── profile.py       # Профиль пользователя
│   │   ├── registration.py  # Регистрация
│   │   └── subscription.py  # Подписки
│   │
│   ├── services/            # Бизнес-логика
│   │   ├── __init__.py
│   │   └── food_analysis_service.py  # Анализ еды
│   │
│   ├── models/              # Модели данных
│   │   └── __init__.py
│   │
│   ├── utils/               # Утилиты
│   │   ├── __init__.py
│   │   ├── macros_calculator.py  # Расчет БЖУ
│   │   ├── progress_bars.py      # Прогресс бары
│   │   └── utils.py              # Общие утилиты
│   │
│   ├── infra/               # Инфраструктура
│   │   └── aiodb.py         # Асинхронная БД
│   │
│   ├── tests/               # Тесты
│   │   ├── test_db_async.py
│   │   ├── test_payment_payload.py
│   │   ├── test_scheduler_lock.py
│   │   └── test_smoke.py
│   │
│   ├── backup/              # 💾 Локальные бекапы (не в Git)
│   │   ├── перед_mini_app/         # Полный бекап (08.10.2025)
│   │   ├── напоминания/            # Система напоминаний (07.10.2025)
│   │   ├── правильный_подсчет/     # Логика подсчета (07.10.2025)
│   │   ├── ложные_срабатывания/    # Фикс обработки (07.10.2025)
│   │   └── промпт_1_детальный/     # Промпт 1 (08.10.2025)
│   │
│   ├── logs/                # 📋 Логи (не в Git)
│   │   └── bot.log
│   │
│   ├── main.py              # 🚀 Главный файл запуска
│   ├── config.py            # Конфигурация бота
│   ├── constants.py         # Константы (текста, timezone, etc.)
│   ├── database.py          # SQLite база (sync)
│   ├── database_async.py    # SQLite база (async)
│   ├── api_client.py        # 🤖 API клиент (3 промпта для ИИ)
│   ├── scheduler.py         # ⏰ Планировщик задач
│   ├── reminder_sender.py   # 🔔 Отправка напоминаний
│   ├── reminder_commands.py # Команды управления напоминаниями
│   ├── bot_functions.py     # Основные функции бота
│   ├── error_handlers.py    # Обработка ошибок
│   ├── logging_config.py    # Настройка логирования
│   ├── validators.py        # Валидаторы ввода
│   ├── voice_handler.py     # Обработка голоса
│   ├── performance_optimizations.py  # Оптимизации
│   │
│   ├── .env                 # 🔐 Переменные окружения (не в Git)
│   ├── .env.example         # Пример переменных
│   ├── .gitignore           # Исключения Git
│   ├── requirements.txt     # Python зависимости
│   ├── runtime.txt          # Python версия (3.12)
│   ├── Procfile             # Railway запуск
│   ├── railway.json         # Railway конфигурация
│   │
│   ├── README.md            # 📖 Основная документация
│   ├── PROJECT_STATUS.md    # Статус проекта
│   ├── BACKUPS_INFO.md      # Информация о бекапах
│   ├── DEPLOYMENT.md        # Инструкции по деплою
│   └── STRUCTURE.md         # Этот файл
│
└── bot_min_app/             # 📱 Копия для Mini App
    └── (полная копия проекта для разработки веб-интерфейса)
```

---

## 🔑 Ключевые файлы

### 1. main.py
Точка входа приложения. Инициализирует:
- Application (Telegram Bot)
- Handlers (команды и callback)
- Scheduler (планировщик задач)
- Database (создание таблиц)

### 2. api_client.py
API клиент для анализа еды. Содержит:
- `analyze_image()` - Промпт 1 (анализ фото)
- `analyze_text()` - Промпт 3 (анализ текста)
- `analyze_photo_supplement()` - Промпт 2 (дополнение)
- `analyze_photo_with_text()` - Комбинированный анализ

### 3. database.py / database_async.py
Работа с SQLite базой данных:
- Users (пользователи)
- Meals (приемы пищи)
- Subscriptions (подписки)
- Статистика и макросы

### 4. scheduler.py
Планировщик задач (APScheduler):
- Сброс дневных счетчиков (00:00)
- Напоминания о завтраке (09:00)
- Напоминания об обеде (14:00)
- Напоминания об ужине (19:00)

### 5. handlers/misc.py
Основной обработчик функционала:
- Анализ фото/текста
- Дополнение анализа
- Подтверждение и сохранение
- Статистика

---

## 🌐 GitHub репозиторий

**URL**: https://github.com/rilya888/calorigram_1

### Последние коммиты:
1. Add BACKUPS_INFO.md (09.10.2025)
2. Add PROJECT_STATUS.md (08.10.2025)
3. Update Prompt 1: Simplified format (08.10.2025)
4. Add Railway deployment configuration (08.10.2025)
5. Initial commit: Calorigram Telegram Bot (08.10.2025)

---

## 📱 Планируемая структура Mini App

```
bot_min_app/
├── backend/                 # Python Telegram Bot (API)
│   └── (текущие файлы)
│
├── frontend/                # Telegram Mini App (новое)
│   ├── index.html
│   ├── manifest.json
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── app.js
│   │   ├── telegram-web-app.js
│   │   └── components/
│   └── assets/
│       └── images/
│
└── api/                     # REST API endpoints (новое)
    ├── routes.py
    ├── auth.py
    └── middleware.py
```

---

**Структура готова для масштабирования и добавления Mini App!** 🚀
