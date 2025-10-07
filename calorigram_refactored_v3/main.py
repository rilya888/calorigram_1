from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, filters
from telegram import BotCommand
from telegram.error import TelegramError

from config import BOT_TOKEN
from bot_functions import (
    start_command, help_command, register_command, profile_command, reset_command, 
    dayreset_command, resetcounters_command, admin_command, add_command, addmeal_command, addvoice_command, subscription_command, 
    terms_command, handle_universal_analysis,
    handle_callback_query, handle_photo, handle_voice, handle_location,
    handle_pre_checkout_query, handle_successful_payment
)
from handlers.misc import handle_stats_today_callback
from reminder_commands import reminder_settings_command, handle_reminder_callback
from error_handlers import error_handler
from logging_config import setup_logging, get_logger
from scheduler import setup_scheduler, start_scheduler, stop_scheduler

# Настройка логирования
setup_logging(
    log_level="INFO",
    log_file="logs/bot.log",
    max_file_size=10 * 1024 * 1024,  # 10MB
    backup_count=5,
    enable_console=True,
    enable_file=True
)
logger = get_logger(__name__)

def main():
    """Основная функция запуска бота"""
    try:
        logger.info("Starting Calorigram bot...")
        
        # Создаем приложение с улучшенными настройками
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .concurrent_updates(True)  # Включаем параллельную обработку обновлений
            .build()
        )
        
        # Устанавливаем команды для меню телеграма (без /admin)
        commands = [
            BotCommand("start", "🏠 Главное меню"),
            BotCommand("help", "❓ Помощь"),
            BotCommand("register", "📝 Регистрация"),
            BotCommand("profile", "👤 Профиль"),
            BotCommand("reset", "🔄 Сброс данных"),
            BotCommand("subscription", "⭐ Подписка"),
            BotCommand("reminders", "🔔 Напоминания"),
            BotCommand("addvoice", "🎤 Анализ голоса"),
            BotCommand("terms", "📄 Условия использования"),
        ]
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("register", register_command))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("reset", reset_command))
        application.add_handler(CommandHandler("subscription", subscription_command))
        application.add_handler(CommandHandler("terms", terms_command))
        application.add_handler(CommandHandler("reminders", reminder_settings_command))
        application.add_handler(CommandHandler("dayreset", dayreset_command))
        application.add_handler(CommandHandler("resetcounters", resetcounters_command))
        application.add_handler(CommandHandler("admin", admin_command))
        application.add_handler(CommandHandler("add", add_command))
        application.add_handler(CommandHandler("addmeal", addmeal_command))
        application.add_handler(CommandHandler("addvoice", addvoice_command))
        
        # Добавляем обработчик callback запросов (более специфичные обработчики идут первыми)
        application.add_handler(CallbackQueryHandler(handle_reminder_callback, pattern="^reminder_|^timezone_"))
        application.add_handler(CallbackQueryHandler(handle_stats_today_callback, pattern="^stats_today$"))
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Добавляем обработчики платежей
        application.add_handler(PreCheckoutQueryHandler(handle_pre_checkout_query))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_successful_payment))
        
        # Добавляем обработчик геолокации
        application.add_handler(MessageHandler(filters.LOCATION, handle_location))
        
        # Добавляем универсальный обработчик анализа (имеет приоритет)
        application.add_handler(MessageHandler(filters.PHOTO | filters.VOICE | (filters.TEXT & ~filters.COMMAND), handle_universal_analysis))
        
        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Настраиваем и запускаем планировщик задач
        if setup_scheduler():
            start_scheduler()
            logger.info("Scheduler started successfully")
        else:
            logger.warning("Failed to start scheduler")
        
        # Выводим информацию о запуске
        logger.info("Bot configuration completed")
        print("Бот @Calorigram_Test_Bot запущен...")
        
        # Запускаем polling с установкой команд
        async def post_init(app):
            """Устанавливаем команды бота после инициализации"""
            await app.bot.set_my_commands(commands)
            logger.info("Bot commands menu configured")
        
        application.post_init = post_init
        
        application.run_polling(
            allowed_updates=["message", "callback_query", "pre_checkout_query"],
            drop_pending_updates=True
        )
        
    except TelegramError as e:
        logger.error(f"Telegram API error: {e}")
        print(f"Ошибка Telegram API: {e}")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        print(f"Ошибка запуска бота: {e}")
        raise
    finally:
        # Останавливаем планировщик при завершении
        stop_scheduler()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Критическая ошибка: {e}")
