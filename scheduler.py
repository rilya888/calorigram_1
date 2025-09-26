"""
Планировщик задач для бота
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from logging_config import get_logger
from database import reset_daily_calorie_checks

logger = get_logger(__name__)

# Создаем планировщик
scheduler = AsyncIOScheduler()

async def reset_daily_counters():
    """Сбрасывает дневные счетчики в полночь"""
    try:
        logger.info("Starting daily reset of calorie checks counter...")
        success = reset_daily_calorie_checks()
        if success:
            logger.info("Daily reset completed successfully")
        else:
            logger.error("Failed to reset daily counters")
    except Exception as e:
        logger.error(f"Error in daily reset: {e}")

def setup_scheduler():
    """Настраивает планировщик задач"""
    try:
        # Добавляем задачу сброса счетчиков в полночь
        scheduler.add_job(
            reset_daily_counters,
            trigger=CronTrigger(hour=0, minute=0),  # Каждый день в 00:00
            id='reset_daily_counters',
            name='Reset daily calorie checks counter',
            replace_existing=True
        )
        
        logger.info("Scheduler configured successfully")
        return True
    except Exception as e:
        logger.error(f"Error setting up scheduler: {e}")
        return False

def start_scheduler():
    """Запускает планировщик"""
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started")
        return True
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return False

def stop_scheduler():
    """Останавливает планировщик"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler stopped")
        return True
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return False
