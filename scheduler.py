"""
Планировщик задач для бота
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from logging_config import get_logger
from database import acquire_db_lock, release_db_lock
from database_async import db_async
from reminder_sender import send_breakfast_reminders, send_lunch_reminders, send_dinner_reminders

import os
from pathlib import Path

SCHEDULER_LOCK_PATH = Path(os.getenv("SCHEDULER_LOCK_PATH", "scheduler.lock"))

def acquire_scheduler_lock() -> bool:
    try:
        if SCHEDULER_LOCK_PATH.exists():
            logger.warning("Scheduler lock exists — another instance may be running. Skipping scheduler start.")
            return False
        SCHEDULER_LOCK_PATH.write_text(str(os.getpid()))
        return True
    except Exception as e:
        logger.error(f"Failed to acquire scheduler lock: {e}")
        return False

def release_scheduler_lock():
    try:
        if SCHEDULER_LOCK_PATH.exists():
            SCHEDULER_LOCK_PATH.unlink()
    except Exception as e:
        logger.error(f"Failed to release scheduler lock: {e}")

logger = get_logger(__name__)

# Создаем планировщик
scheduler = AsyncIOScheduler()

async def reset_daily_counters():
    """Сбрасывает дневные счетчики в полночь"""
    try:
        logger.info("Starting daily reset of calorie checks counter...")
        success = await db_async.reset_daily_calorie_checks()
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
        
        # Добавляем задачи отправки напоминаний о приемах пищи
        scheduler.add_job(
            send_breakfast_reminders,
            trigger=CronTrigger(hour=9, minute=0),  # Каждый день в 09:00
            id='breakfast_reminders',
            name='Send breakfast reminders',
            replace_existing=True
        )
        
        scheduler.add_job(
            send_lunch_reminders,
            trigger=CronTrigger(hour=14, minute=0),  # Каждый день в 14:00
            id='lunch_reminders',
            name='Send lunch reminders',
            replace_existing=True
        )
        
        scheduler.add_job(
            send_dinner_reminders,
            trigger=CronTrigger(hour=19, minute=0),  # Каждый день в 19:00
            id='dinner_reminders',
            name='Send dinner reminders',
            replace_existing=True
        )
        
        logger.info("Scheduler configured successfully with reminders")
        return True
    except Exception as e:
        logger.error(f"Error setting up scheduler: {e}")
        return False

def start_scheduler():
    """Запускает планировщик"""
    try:
        if not acquire_scheduler_lock():
            return False
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
        release_scheduler_lock()
        return True
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return False
