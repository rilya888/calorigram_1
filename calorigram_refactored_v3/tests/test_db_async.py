
import pytest
from database_async import db_async

@pytest.mark.asyncio
async def test_async_user_cycle():
    # Просто проверим, что запросы не падают (данных может не быть)
    user = await db_async.get_user_by_telegram_id(9999999)
    assert user is None
