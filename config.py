"""
Конфигурация для телеграм бота Calorigram
Использует переменные окружения для безопасности
"""
import os
from dotenv import load_dotenv
from constants import API_TIMEOUT, MAX_API_RETRIES, MAX_IMAGE_SIZE, MAX_AUDIO_SIZE
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

# Дополнительные API ключи для распознавания речи
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")

API_KEYS = {
    "nebius_api": NEBUIS_API_KEY,
    "openai_api": OPENAI_API_KEY,
    "assemblyai_api": ASSEMBLYAI_API_KEY
}

# API настройки
BASE_URL = os.getenv("BASE_URL", "https://api.studio.nebius.ai/v1/")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "users.db")

# Admin IDs
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "160308091")
try:
    ADMIN_IDS = [int(id_str.strip()) for id_str in ADMIN_IDS_STR.split(",") if id_str.strip()]
except ValueError:
    ADMIN_IDS = [160308091]  # Fallback to default admin ID

# API Settings are imported from constants.py