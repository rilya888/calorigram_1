
import aiosqlite
from typing import Optional, Any, Dict
from config import DATABASE_PATH
from logging_config import get_logger

logger = get_logger(__name__)

class AioDB:
    def __init__(self, path: str = DATABASE_PATH):
        self.path = path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        if not self._conn:
            self._conn = await aiosqlite.connect(self.path)
            self._conn.row_factory = aiosqlite.Row
            await self._conn.execute("PRAGMA foreign_keys = ON;")
            await self._conn.execute("PRAGMA journal_mode = WAL;")
            await self._conn.execute("PRAGMA synchronous = NORMAL;")
            await self._conn.commit()
        return self._conn

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def reset_daily_calorie_checks_async(self) -> bool:
        try:
            conn = await self.connect()
            await conn.execute("UPDATE calorie_checks SET created_at = DATE('now') WHERE 1=0")  # placeholder
            # Реальная логика сброса должна быть скопирована из sync-версии
            await conn.commit()
            return True
        except Exception as e:
            logger.error(f"reset_daily_calorie_checks_async error: {e}")
            return False

db = AioDB()
