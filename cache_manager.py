"""
Модуль для управления кэшем
"""
import time
import hashlib
from typing import Dict, Any, Optional
from logging_config import get_logger
from performance_optimizations import memory_optimizer

logger = get_logger(__name__)

class CacheManager:
    """Менеджер кэша для оптимизации производительности"""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
    
    def _generate_key(self, data: str) -> str:
        """Генерирует ключ кэша на основе данных"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Получает данные из кэша"""
        try:
            if key not in self.cache:
                return None
            
            cache_entry = self.cache[key]
            current_time = time.time()
            
            # Проверяем TTL
            if current_time - cache_entry['timestamp'] > cache_entry['ttl']:
                del self.cache[key]
                return None
            
            logger.debug(f"Cache hit for key: {key[:8]}...")
            return cache_entry['data']
            
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Сохраняет данные в кэш"""
        try:
            # Очищаем кэш если он превышает максимальный размер
            if len(self.cache) >= self.max_size:
                memory_optimizer.clear_cache_if_needed(self.cache, self.max_size)
            
            cache_ttl = ttl if ttl is not None else self.default_ttl
            self.cache[key] = {
                'data': data,
                'timestamp': time.time(),
                'ttl': cache_ttl
            }
            
            logger.debug(f"Cache set for key: {key[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Удаляет данные из кэша"""
        try:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache deleted for key: {key[:8]}...")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def clear_expired(self) -> int:
        """Очищает устаревшие записи из кэша"""
        try:
            current_time = time.time()
            expired_keys = []
            
            for key, cache_entry in self.cache.items():
                if current_time - cache_entry['timestamp'] > cache_entry['ttl']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cleared {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        try:
            current_time = time.time()
            total_entries = len(self.cache)
            expired_entries = 0
            
            for cache_entry in self.cache.values():
                if current_time - cache_entry['timestamp'] > cache_entry['ttl']:
                    expired_entries += 1
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries,
                'cache_size_mb': sum(len(str(entry['data']).encode('utf-8')) for entry in self.cache.values()) / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    def clear_all(self) -> bool:
        """Очищает весь кэш"""
        try:
            self.cache.clear()
            logger.info("Cache cleared completely")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

# Глобальные экземпляры кэша для разных типов данных
user_cache = CacheManager(default_ttl=600, max_size=500)  # 10 минут для пользователей
analysis_cache = CacheManager(default_ttl=1800, max_size=200)  # 30 минут для анализов
stats_cache = CacheManager(default_ttl=300, max_size=100)  # 5 минут для статистики

