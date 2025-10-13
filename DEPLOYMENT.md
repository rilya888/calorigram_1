# Инструкция по развертыванию Calorigram Bot

## 🚀 Быстрый старт

### 1. Подготовка окружения

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd calorigram_backup_20250919_103934_рассылка

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корневой директории:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here

# API Configuration
NEBUIS_API_KEY=your_nebius_api_key_here
BASE_URL=https://api.studio.nebius.ai/v1/

# Database Configuration
DATABASE_PATH=users.db

# Test Mode (True/False)
TEST_MODE=True

# Admin IDs (comma-separated)
ADMIN_IDS=160308091
```

### 3. Получение токенов

#### Telegram Bot Token:
1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `.env`

#### Nebius API Key:
1. Зарегистрируйтесь на [Nebius](https://nebius.ai)
2. Создайте API ключ
3. Скопируйте ключ в `.env`

### 4. Запуск бота

```bash
python main.py
```

## 🔧 Конфигурация

### Настройка логирования

Логи настраиваются в `main.py`:

```python
setup_logging(
    log_level="INFO",           # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_file="logs/bot.log",    # Путь к файлу лога
    max_file_size=10 * 1024 * 1024,  # Максимальный размер файла
    backup_count=5,             # Количество резервных файлов
    enable_console=True,        # Вывод в консоль
    enable_file=True           # Запись в файл
)
```

### Настройка базы данных

База данных SQLite создается автоматически. Настройки в `config.py`:

```python
DATABASE_PATH = os.getenv("DATABASE_PATH", "users.db")
```

### Настройка API

Настройки API в `config.py`:

```python
API_TIMEOUT = 30        # Таймаут запросов
MAX_RETRIES = 3         # Количество повторных попыток
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # Максимальный размер изображения
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # Максимальный размер аудио
```

## 🐳 Docker развертывание

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs

CMD ["python", "main.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  calorigram-bot:
    build: .
    container_name: calorigram-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - NEBUIS_API_KEY=${NEBUIS_API_KEY}
      - BASE_URL=${BASE_URL}
      - DATABASE_PATH=${DATABASE_PATH}
      - TEST_MODE=${TEST_MODE}
      - ADMIN_IDS=${ADMIN_IDS}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
```

### Запуск с Docker

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## 🌐 Production развертывание

### 1. Системные требования

- Python 3.11+
- 1GB RAM минимум
- 10GB свободного места
- Стабильное интернет-соединение

### 2. Настройка systemd (Linux)

Создайте файл `/etc/systemd/system/calorigram-bot.service`:

```ini
[Unit]
Description=Calorigram Telegram Bot
After=network.target

[Service]
Type=simple
User=calorigram
WorkingDirectory=/opt/calorigram-bot
Environment=PATH=/opt/calorigram-bot/venv/bin
ExecStart=/opt/calorigram-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Управление сервисом

```bash
# Включить автозапуск
sudo systemctl enable calorigram-bot

# Запустить сервис
sudo systemctl start calorigram-bot

# Проверить статус
sudo systemctl status calorigram-bot

# Остановить сервис
sudo systemctl stop calorigram-bot

# Перезапустить сервис
sudo systemctl restart calorigram-bot
```

### 4. Мониторинг

```bash
# Просмотр логов
sudo journalctl -u calorigram-bot -f

# Просмотр логов файла
tail -f logs/bot.log
```

## 🔒 Безопасность

### 1. Переменные окружения

- Никогда не коммитьте `.env` файл
- Используйте сильные пароли для API ключей
- Регулярно обновляйте токены

### 2. Файрвол

```bash
# Разрешить только необходимые порты
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP (если нужен)
sudo ufw allow 443   # HTTPS (если нужен)
sudo ufw enable
```

### 3. Резервное копирование

```bash
# Создание резервной копии базы данных
cp users.db backup/users_$(date +%Y%m%d_%H%M%S).db

# Автоматическое резервное копирование (crontab)
0 2 * * * /opt/calorigram-bot/backup.sh
```

## 📊 Мониторинг и логирование

### 1. Логи

Логи сохраняются в:
- `logs/bot.log` - основной лог
- `logs/bot.log.1`, `logs/bot.log.2` и т.д. - архивные логи

### 2. Метрики

Бот логирует:
- Действия пользователей
- API запросы
- Ошибки
- Производительность

### 3. Алерты

Настройте уведомления для:
- Критических ошибок
- Высокой нагрузки
- Недоступности API

## 🛠️ Обслуживание

### 1. Обновление

```bash
# Остановить бота
sudo systemctl stop calorigram-bot

# Создать резервную копию
cp -r /opt/calorigram-bot /opt/calorigram-bot.backup

# Обновить код
git pull origin main

# Установить новые зависимости
pip install -r requirements.txt

# Запустить бота
sudo systemctl start calorigram-bot
```

### 2. Очистка логов

```bash
# Очистка старых логов
find logs/ -name "*.log.*" -mtime +30 -delete
```

### 3. Оптимизация базы данных

```bash
# Сжатие базы данных SQLite
sqlite3 users.db "VACUUM;"
```

## 🆘 Устранение неполадок

### 1. Бот не запускается

```bash
# Проверить логи
sudo journalctl -u calorigram-bot -n 50

# Проверить переменные окружения
cat .env

# Проверить зависимости
pip list
```

### 2. Ошибки API

- Проверить валидность токенов
- Проверить подключение к интернету
- Проверить лимиты API

### 3. Ошибки базы данных

```bash
# Проверить целостность базы данных
sqlite3 users.db "PRAGMA integrity_check;"

# Восстановить из резервной копии
cp backup/users_YYYYMMDD_HHMMSS.db users.db
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи
2. Проверьте документацию
3. Создайте issue в репозитории
4. Обратитесь к администратору

## 🔄 Обновления

### Версия 2.0 (Текущая)

- ✅ Обновлен до python-telegram-bot 21.7
- ✅ Добавлена поддержка Telegram Bot API 9.2
- ✅ Улучшена система логирования
- ✅ Добавлена валидация данных
- ✅ Оптимизирована работа с API
- ✅ Добавлены современные функции

### Планируемые обновления

- 🔄 Web App интерфейс
- 🔄 Мобильное приложение
- 🔄 Расширенная аналитика
- 🔄 Интеграция с фитнес-трекерами
