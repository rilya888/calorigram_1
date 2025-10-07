
from database import ensure_lock_table, acquire_db_lock, release_db_lock

def test_db_lock_cycle():
    ensure_lock_table()
    assert acquire_db_lock("ci_lock", "pytest") is True
    # Second acquire should fail
    assert acquire_db_lock("ci_lock", "pytest") is False
    assert release_db_lock("ci_lock") is True
