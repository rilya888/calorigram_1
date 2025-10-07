
import aiosqlite
from typing import Optional, Tuple, Any, List, Dict
from logging_config import get_logger
from config import DATABASE_PATH

logger = get_logger(__name__)

class DBAsync:
    def __init__(self, path: str = DATABASE_PATH):
        self.path = path

    async def connect(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(self.path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.execute("PRAGMA journal_mode = WAL;")
        await conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    # --- Users ---
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        async with await self.connect() as conn:
            async with conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def create_user_with_goal(self, telegram_id: int, age: int, height: int, weight: float, gender: str, activity_level: str, goal: str) -> bool:
        async with await self.connect() as conn:
            try:
                await conn.execute('''
                    INSERT INTO users (telegram_id, age, height, weight, gender, activity_level, goal)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (telegram_id, age, height, weight, gender, activity_level, goal))
                await conn.commit()
                return True
            except Exception as e:
                logger.error(f"create_user_with_goal async error: {e}")
                return False

    # --- Meals ---
    async def add_meal(self, telegram_id: int, meal_type: str, meal_name: str, dish_name: str,
                       calories: int, protein: float, fat: float, carbs: float, analysis_type: str) -> bool:
        async with await self.connect() as conn:
            try:
                await conn.execute('''
                    INSERT INTO meals (telegram_id, meal_type, meal_name, dish_name, calories, protein, fat, carbs, analysis_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (telegram_id, meal_type, meal_name, dish_name, calories, protein, fat, carbs, analysis_type))
                await conn.commit()
                return True
            except Exception as e:
                logger.error(f"add_meal async error: {e}")
                return False

    async def get_daily_calories(self, telegram_id: int) -> int:
        async with await self.connect() as conn:
            async with conn.execute('''
                SELECT COALESCE(SUM(calories), 0) as total
                FROM meals
                WHERE telegram_id = ? AND DATE(created_at) = DATE('now','localtime')
            ''', (telegram_id,)) as cur:
                row = await cur.fetchone()
                return int(row["total"]) if row else 0

    # --- Locks ---
    async def ensure_lock_table(self) -> bool:
        try:
            async with await self.connect() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS locks (
                        name TEXT PRIMARY KEY,
                        owner TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"ensure_lock_table async error: {e}")
            return False

    async def acquire_db_lock(self, name: str, owner: str) -> bool:
        await self.ensure_lock_table()
        try:
            async with await self.connect() as conn:
                await conn.execute("INSERT INTO locks (name, owner) VALUES (?, ?)", (name, owner))
                await conn.commit()
                return True
        except aiosqlite.IntegrityError:
            logger.warning(f"Lock '{name}' already held (async)")
            return False
        except Exception as e:
            logger.error(f"acquire_db_lock async error: {e}")
            return False

    async def release_db_lock(self, name: str) -> bool:
        try:
            async with await self.connect() as conn:
                await conn.execute("DELETE FROM locks WHERE name = ?", (name,))
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"release_db_lock async error: {e}")
            return False

    # --- Daily reset (example) ---
    async def reset_daily_calorie_checks(self) -> bool:
        try:
            async with await self.connect() as conn:
                # Здесь разместите реальную логику сброса (по аналогии с sync-версией)
                # Пример: очистка служебной таблицы за текущий день
                # await conn.execute("DELETE FROM calorie_checks WHERE DATE(created_at) < DATE('now','localtime')")
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"reset_daily_calorie_checks async error: {e}")
            return False

db_async = DBAsync()
