"""
Конфигурация для телеграм бота Calorigram
Использует переменные окружения для безопасности
"""
import os
from dotenv import load_dotenv
from typing import List

# Загружаем переменные окружения из .env файла
load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

# Test Mode
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"

# API Configuration
NEBUIS_API_KEY = os.getenv("NEBUIS_API_KEY", "")
if not NEBUIS_API_KEY:
    raise ValueError("NEBUIS_API_KEY не найден в переменных окружения!")

API_KEYS = {
    "nebius_api": NEBUIS_API_KEY
}

# API настройки
BASE_URL = os.getenv("BASE_URL", "https://inference.nebius.ai/v1/")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "users.db")

# Admin IDs
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "160308091")
try:
    ADMIN_IDS = [int(id_str.strip()) for id_str in ADMIN_IDS_STR.split(",") if id_str.strip()]
except ValueError:
    ADMIN_IDS = [160308091]  # Fallback to default admin ID

# API Settings
API_TIMEOUT = 30
MAX_RETRIES = 3
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB
