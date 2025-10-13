"""
Дополнительные оптимизации производительности для бота Calorigram
"""
import asyncio
import time
from functools import wraps
from typing import Callable, Any
from logging_config import get_logger

logger = get_logger(__name__)

def performance_monitor(func: Callable) -> Callable:
    """Декоратор для мониторинга производительности функций"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Function {func.__name__} executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Function {func.__name__} executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

class RateLimiter:
    """Класс для ограничения частоты запросов"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def is_allowed(self) -> bool:
        """Проверяет, можно ли выполнить запрос"""
        now = time.time()
        # Удаляем старые запросы
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
    
    def get_wait_time(self) -> float:
        """Возвращает время ожидания до следующего разрешенного запроса"""
        if not self.requests:
            return 0
        
        oldest_request = min(self.requests)
        return max(0, self.time_window - (time.time() - oldest_request))

class MemoryOptimizer:
    """Класс для оптимизации использования памяти"""
    
    @staticmethod
    def clear_cache_if_needed(cache: dict, max_size: int = 1000) -> None:
        """Очищает кэш если он превышает максимальный размер"""
        if len(cache) > max_size:
            # Удаляем 20% самых старых записей
            items_to_remove = len(cache) // 5
            sorted_items = sorted(cache.items(), key=lambda x: x[1][1] if isinstance(x[1], tuple) else 0)
            for key, _ in sorted_items[:items_to_remove]:
                cache.pop(key, None)
            logger.info(f"Cleared {items_to_remove} items from cache")
    
    @staticmethod
    def optimize_strings(text: str, max_length: int = 1000) -> str:
        """Оптимизирует строки, обрезая и очищая их"""
        if not text:
            return ""
        
        # Удаляем лишние пробелы
        text = ' '.join(text.split())
        
        # Обрезаем до максимальной длины
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"String truncated to {max_length} characters")
        
        return text

class DatabaseOptimizer:
    """Класс для оптимизации работы с базой данных"""
    
    @staticmethod
    def batch_insert(conn, table: str, data: list, batch_size: int = 100) -> bool:
        """Выполняет пакетную вставку данных"""
        try:
            if not data:
                return True
            
            cursor = conn.cursor()
            
            # Разбиваем данные на батчи
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                placeholders = ', '.join(['?' for _ in batch[0]])
                query = f"INSERT INTO {table} VALUES ({placeholders})"
                cursor.executemany(query, batch)
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error in batch insert: {e}")
            return False
    
    @staticmethod
    def optimize_queries(conn) -> None:
        """Применяет оптимизации для SQLite"""
        try:
            cursor = conn.cursor()
            
            # Включаем WAL режим для лучшей производительности
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Устанавливаем размер кэша
            cursor.execute("PRAGMA cache_size=10000")
            
            # Оптимизируем синхронизацию
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # Используем память для временных таблиц
            cursor.execute("PRAGMA temp_store=MEMORY")
            
            # Включаем внешние ключи
            cursor.execute("PRAGMA foreign_keys=ON")
            
            logger.info("Database optimizations applied")
        except Exception as e:
            logger.error(f"Error applying database optimizations: {e}")

# Глобальные экземпляры для использования в приложении
rate_limiter = RateLimiter(max_requests=10, time_window=60)  # 10 запросов в минуту
memory_optimizer = MemoryOptimizer()
db_optimizer = DatabaseOptimizer()
