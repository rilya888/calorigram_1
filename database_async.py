
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

    async def create_user_with_goal(self, telegram_id: int, name: str, age: int, height: float, weight: float, gender: str, activity_level: str, daily_calories: int, goal: str, target_calories: int) -> bool:
        async with await self.connect() as conn:
            try:
                await conn.execute('''
                    INSERT INTO users (telegram_id, name, age, height, weight, gender, activity_level, daily_calories, goal, target_calories)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (telegram_id, name, age, height, weight, gender, activity_level, daily_calories, goal, target_calories))
                await conn.commit()
                return True
            except aiosqlite.IntegrityError as e:
                logger.warning(f"User with telegram_id {telegram_id} already exists: {e}")
                return False
            except Exception as e:
                logger.error(f"create_user_with_goal async error: {e}")
                return False

    # --- Meals ---
    async def add_meal(self, telegram_id: int, meal_type: str, meal_name: str, dish_name: str,
                       calories: int, protein: float = 0.0, fat: float = 0.0, carbs: float = 0.0, analysis_type: str = "unknown") -> bool:
        async with await self.connect() as conn:
            try:
                await conn.execute('''
                    INSERT INTO meals (telegram_id, meal_type, meal_name, dish_name, calories, protein, fat, carbs, analysis_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (telegram_id, meal_type, meal_name, dish_name, calories, protein, fat, carbs, analysis_type))
                await conn.commit()
                return True
            except aiosqlite.IntegrityError as e:
                logger.error(f"Database integrity error adding meal: {e}")
                return False
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

    # --- Daily reset ---
    async def reset_daily_calorie_checks(self) -> bool:
        try:
            async with await self.connect() as conn:
                # Удаляем записи старше 1 дня
                await conn.execute('''
                    DELETE FROM calorie_checks 
                    WHERE created_at < DATE('now', '-1 day')
                ''')
                await conn.commit()
                return True
        except aiosqlite.Error as e:
            logger.error(f"Database error in reset_daily_calorie_checks: {e}")
            return False
        except Exception as e:
            logger.error(f"reset_daily_calorie_checks async error: {e}")
            return False

    # --- Subscription management ---
    async def check_user_subscription(self, telegram_id: int) -> Dict[str, Any]:
        """Проверяет статус подписки пользователя"""
        try:
            async with await self.connect() as conn:
                async with conn.execute('''
                    SELECT subscription_type, subscription_expires_at, is_premium, created_at
                    FROM users 
                    WHERE telegram_id = ?
                ''', (telegram_id,)) as cur:
                    row = await cur.fetchone()
                    if not row:
                        return {'is_active': False, 'type': 'none', 'expires_at': None}
                    
                    subscription_type, expires_at, is_premium, created_at = row
                    
                    # Логика проверки подписки аналогична синхронной версии
                    if subscription_type == 'trial':
                        if expires_at:
                            # Проверяем, не истек ли триальный период
                            async with conn.execute('SELECT datetime("now") > ?', (expires_at,)) as check_cur:
                                is_expired = await check_cur.fetchone()
                                if is_expired[0]:
                                    return {'is_active': False, 'type': 'trial_expired', 'expires_at': expires_at}
                                else:
                                    return {'is_active': True, 'type': 'trial', 'expires_at': expires_at}
                        else:
                            return {'is_active': True, 'type': 'trial', 'expires_at': None}
                    elif subscription_type == 'premium' and is_premium:
                        if expires_at:
                            async with conn.execute('SELECT datetime("now") > ?', (expires_at,)) as check_cur:
                                is_expired = await check_cur.fetchone()
                                if is_expired[0]:
                                    return {'is_active': False, 'type': 'premium_expired', 'expires_at': expires_at}
                                else:
                                    return {'is_active': True, 'type': 'premium', 'expires_at': expires_at}
                        else:
                            return {'is_active': True, 'type': 'premium', 'expires_at': None}
                    
                    return {'is_active': False, 'type': 'none', 'expires_at': None}
                    
        except aiosqlite.Error as e:
            logger.error(f"Database error checking user subscription: {e}")
            return {'is_active': False, 'type': 'error', 'expires_at': None}
        except Exception as e:
            logger.error(f"Error checking user subscription: {e}")
            return {'is_active': False, 'type': 'error', 'expires_at': None}

db_async = DBAsync()
