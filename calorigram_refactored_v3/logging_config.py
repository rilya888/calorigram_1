"""
Конфигурация логирования для бота Calorigram
"""
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для консольного вывода"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Добавляем цвет к уровню логирования
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        
        return super().format(record)

def setup_logging(
    log_level: str = "INFO",
    log_file: str = "bot.log",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True
) -> None:
    """
    Настраивает систему логирования с улучшенной обработкой ошибок
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу лога
        max_file_size: Максимальный размер файла лога в байтах
        backup_count: Количество резервных файлов логов
        enable_console: Включить вывод в консоль
        enable_file: Включить запись в файл
    """
    
    try:
        # Создаем директорию для логов, если её нет
        log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else "."
        os.makedirs(log_dir, exist_ok=True)
        
        # Настраиваем корневой логгер
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Очищаем существующие обработчики
        root_logger.handlers.clear()
        
        # Формат сообщений с улучшенной информацией
        log_format = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(filename)s:%(lineno)d - %(funcName)s - %(message)s'
        )
        
        # Создаем форматтеры
        file_formatter = logging.Formatter(log_format)
        console_formatter = ColoredFormatter(log_format)
        
        # Обработчик для файла с ротацией
        if enable_file:
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setFormatter(file_formatter)
                file_handler.setLevel(getattr(logging, log_level.upper()))
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Failed to setup file logging: {e}")
        
        # Обработчик для консоли
        if enable_console:
            try:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(console_formatter)
                console_handler.setLevel(getattr(logging, log_level.upper()))
                root_logger.addHandler(console_handler)
            except Exception as e:
                print(f"Warning: Failed to setup console logging: {e}")
        
        # Настраиваем логирование для внешних библиотек
        logging.getLogger('telegram').setLevel(logging.WARNING)
        logging.getLogger('aiohttp').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        
        # Логируем информацию о настройке
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured - Level: {log_level}, File: {log_file}")
        
    except Exception as e:
        print(f"Critical error in logging setup: {e}")
        # Fallback к базовому логированию
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

def get_logger(name: str) -> logging.Logger:
    """Получает логгер с указанным именем"""
    return logging.getLogger(name)

class BotLogger:
    """Специализированный логгер для бота"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_user_action(self, user_id: int, action: str, details: Optional[str] = None):
        """Логирует действие пользователя"""
        message = f"User {user_id} - {action}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_api_request(self, endpoint: str, status: int, duration: Optional[float] = None):
        """Логирует запрос к API"""
        message = f"API Request - {endpoint} - Status: {status}"
        if duration:
            message += f" - Duration: {duration:.2f}s"
        self.logger.info(message)
    
    def log_error(self, error: Exception, context: Optional[str] = None):
        """Логирует ошибку с контекстом"""
        message = f"Error: {type(error).__name__} - {str(error)}"
        if context:
            message += f" - Context: {context}"
        self.logger.error(message, exc_info=True)
    
    def log_performance(self, operation: str, duration: float, details: Optional[str] = None):
        """Логирует производительность операции"""
        message = f"Performance - {operation} - Duration: {duration:.2f}s"
        if details:
            message += f" - {details}"
        self.logger.info(message)

# Создаем глобальный логгер бота
bot_logger = BotLogger("calorigram_bot")
