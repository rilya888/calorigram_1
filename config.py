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

# API Configuration - OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не найден в переменных окружения!")

# Дополнительные API ключи (для совместимости)
NEBUIS_API_KEY = os.getenv("NEBUIS_API_KEY", "")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")

API_KEYS = {
    "openai_api": OPENAI_API_KEY,
    "nebius_api": NEBUIS_API_KEY,
    "assemblyai_api": ASSEMBLYAI_API_KEY
}

# API настройки - OpenAI
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Модель для анализа текста и изображений
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")  # Модель для анализа изображений
OPENAI_WHISPER_MODEL = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")  # Модель для распознавания речи

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "users.db")

# Admin IDs
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "160308091")
try:
    ADMIN_IDS = [int(id_str.strip()) for id_str in ADMIN_IDS_STR.split(",") if id_str.strip()]
except ValueError:
    ADMIN_IDS = [160308091]  # Fallback to default admin ID

# API Settings are imported from constants.py