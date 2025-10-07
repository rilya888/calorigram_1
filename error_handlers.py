"""
Обработчики ошибок для бота Calorigram
"""
from logging_config import get_logger
import traceback
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, NetworkError, TimedOut, BadRequest

logger = get_logger(__name__)

class ErrorHandler:
    """Класс для обработки различных типов ошибок"""
    
    @staticmethod
    async def handle_telegram_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: TelegramError) -> bool:
        """Обрабатывает ошибки Telegram API"""
        try:
            if isinstance(error, BadRequest):
                logger.warning(f"Bad request error: {error}")
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "❌ Неверный запрос. Попробуйте еще раз."
                    )
                return True
            
            elif isinstance(error, TimedOut):
                logger.warning(f"Timeout error: {error}")
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "⏱️ Время ожидания истекло. Попробуйте еще раз."
                    )
                return True
            
            elif isinstance(error, NetworkError):
                logger.error(f"Network error: {error}")
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "🌐 Ошибка сети. Проверьте подключение к интернету."
                    )
                return True
            
            else:
                logger.error(f"Telegram API error: {error}")
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "❌ Произошла ошибка. Попробуйте позже."
                    )
                return True
                
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            return False
    
    @staticmethod
    async def handle_general_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> bool:
        """Обрабатывает общие ошибки"""
        try:
            logger.error(f"Unhandled error: {error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ Произошла неожиданная ошибка. Попробуйте позже или обратитесь к администратору."
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error in general error handler: {e}")
            return False
    
    @staticmethod
    async def handle_api_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> bool:
        """Обрабатывает ошибки внешних API"""
        try:
            logger.error(f"API error: {error}")
            
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "🤖 Ошибка анализа ИИ. Попробуйте позже или используйте другой способ."
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error in API error handler: {e}")
            return False
    
    @staticmethod
    async def handle_database_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> bool:
        """Обрабатывает ошибки базы данных"""
        try:
            logger.error(f"Database error: {error}")
            
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "💾 Ошибка базы данных. Попробуйте позже."
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error in database error handler: {e}")
            return False

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главный обработчик ошибок"""
    error = context.error
    
    if isinstance(error, TelegramError):
        await ErrorHandler.handle_telegram_error(update, context, error)
    elif isinstance(error, (ConnectionError, TimeoutError)):
        await ErrorHandler.handle_api_error(update, context, error)
    elif "database" in str(error).lower() or "sqlite" in str(error).lower():
        await ErrorHandler.handle_database_error(update, context, error)
    else:
        await ErrorHandler.handle_general_error(update, context, error)

