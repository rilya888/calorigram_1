"""
Асинхронный клиент для работы с внешними API
"""
import asyncio
import base64
import hashlib
import time
from logging_config import get_logger
from typing import Optional, Dict, Any
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from config import API_KEYS, BASE_URL, API_TIMEOUT, MAX_API_RETRIES, MAX_IMAGE_SIZE
from performance_optimizations import rate_limiter

logger = get_logger(__name__)

class APIClient:
    """Асинхронный клиент для работы с API"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.api_key = API_KEYS.get("nebius_api")
        self.timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Tuple[str, float]] = {}  # Кэш для результатов
        self.cache_ttl = 300  # TTL кэша в секундах (5 минут)
        self.max_cache_size = 1000  # Максимальный размер кэша
    
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            import ssl
            import os
            
            # Создаем SSL контекст с настройками безопасности
            ssl_context = ssl.create_default_context()
            
            # В продакшене включаем проверку сертификатов, в тесте можно отключить
            if os.getenv("TEST_MODE", "False").lower() == "true":
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            else:
                ssl_context.check_hostname = True
                ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            # Ограничиваем протоколы для безопасности
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            connector = aiohttp.TCPConnector(
                ssl=ssl_context, 
                limit=100, 
                limit_per_host=30,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self.session = aiohttp.ClientSession(
                timeout=self.timeout, 
                connector=connector,
                headers={'User-Agent': 'CalorigramBot/1.0'}
            )
            logger.info("APIClient session created successfully")
            return self
        except Exception as e:
            logger.error(f"Failed to create APIClient session: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        try:
            if self.session:
                await self.session.close()
                logger.info("APIClient session closed successfully")
        except Exception as e:
            logger.error(f"Error closing APIClient session: {e}")
        finally:
            # Очищаем кэш при выходе
            self.cache.clear()
    
    def _get_cache_key(self, data: bytes) -> str:
        """Генерирует ключ кэша на основе данных"""
        return hashlib.md5(data).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Получает данные из кэша"""
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"Cache hit for key: {cache_key[:8]}...")
                return result
            else:
                # Удаляем устаревший кэш
                del self.cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, result: str) -> None:
        """Сохраняет данные в кэш"""
        # Очищаем кэш если он превышает максимальный размер
        if len(self.cache) >= self.max_cache_size:
            # Удаляем самые старые записи
            oldest_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k][1])[:100]
            for key in oldest_keys:
                del self.cache[key]
        
        self.cache[cache_key] = (result, time.time())
        logger.info(f"Cache set for key: {cache_key[:8]}...")
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Выполняет HTTP запрос с повторными попытками"""
        if not self.session:
            raise RuntimeError("APIClient не инициализирован. Используйте async with")
        
        # Проверяем rate limiting
        if not rate_limiter.is_allowed():
            wait_time = rate_limiter.get_wait_time()
            logger.warning(f"Rate limit exceeded, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        
        for attempt in range(MAX_API_RETRIES):
            try:
                logger.info(f"Making request attempt {attempt + 1}/{MAX_API_RETRIES} to {url}")
                async with self.session.request(method, url, **kwargs) as response:
                    logger.info(f"Response status: {response.status}")
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Response received successfully, size: {len(str(result))}")
                        return result
                    elif response.status == 429:  # Rate limit
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limit hit, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_text = await response.text()
                        logger.error(f"API request failed with status {response.status}: {error_text}")
                        return None
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{MAX_API_RETRIES})")
                if attempt < MAX_API_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except aiohttp.ClientError as e:
                logger.error(f"HTTP client error: {e}")
                if attempt < MAX_API_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except Exception as e:
                logger.error(f"Unexpected request error: {e}")
                if attempt < MAX_API_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        return None
    
    async def analyze_image(self, image_data: bytes) -> Optional[str]:
        """Анализирует изображение еды"""
        try:
            # Валидация размера файла
            if not image_data:
                logger.error("Empty image data provided")
                return None
                
            if len(image_data) > MAX_IMAGE_SIZE:
                logger.error(f"Image too large: {len(image_data)} bytes (max: {MAX_IMAGE_SIZE})")
                return None
            
            # Проверяем минимальный размер (должен быть больше 0)
            if len(image_data) < 100:
                logger.error("Image too small, might be corrupted")
                return None
            
            # Проверяем кэш
            cache_key = self._get_cache_key(image_data)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            # Кодируем изображение в base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "Qwen/Qwen2.5-VL-72B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": """Ты эксперт по анализу еды и подсчету калорий. 
                        Проанализируй изображение еды и предоставь информацию в следующем формате:
                        
                        🍽️ Анализ блюда:

                        Название: [название блюда]
                        Вес: [общий вес блюда]г
                        Калорийность: [ОБЩАЯ калорийность для всего количества] ккал

                        📊 БЖУ на 100г:
                        • Белки: [количество]г
                        • Жиры: [количество]г  
                        • Углеводы: [количество]г

                        📈 Общее БЖУ в блюде:
                        • Белки: [общее количество]г
                        • Жиры: [общее количество]г
                        • Углеводы: [общее количество]г
                        
                        КРИТИЧЕСКИ ВАЖНО - СТАНДАРТНЫЕ КАЛОРИЙНОСТИ:
                        • Мясо жаренное: 250 ккал/100г
                        • Яблоки: 50 ккал/100г  
                        • Халва: 450 ккал/100г
                        
                        МАТЕМАТИЧЕСКИЕ ПРАВИЛА (ОБЯЗАТЕЛЬНО!):
                        1. Сначала определи калорийность на 100г для данного продукта
                        2. Затем рассчитай ОБЩУЮ калорийность: (общий_вес_в_граммах ÷ 100) × калорийность_на_100г
                        3. НИКОГДА не округляй промежуточные результаты!
                        4. ОДИНАКОВЫЙ вес = ОДИНАКОВАЯ калорийность!
                        
                        ОБЯЗАТЕЛЬНЫЕ ПРИМЕРЫ:
                        • "яблоко 3 кг" = 3000г, 1500 ккал (3000÷100×50=1500)
                        • "яблоки 3 кг" = 3000г, 1500 ккал (3000÷100×50=1500)
                        
                        КОНТРОЛЬНАЯ ФОРМУЛА:
                        Общая калорийность = (вес_в_г ÷ 100) × калорийность_на_100г
                        
                        ВАЖНО: Рассчитай калорийность для ВСЕГО видимого количества еды на фото, а не только для 100г!
                        НЕ добавляй никаких дополнительных пояснений, расчетов или объяснений!
                        НЕ используй обратные слеши (\\) в числах!
                        
                        Пример правильного формата:
                        • Белки: 0,3г (не 03г)
                        • Жиры: 2,5г (не 25г)
                        • Углеводы: 13,8г (не 138г)
                        
                        Используй запятую как десятичный разделитель: 0,3г вместо 0.3г"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Проанализируй это изображение еды и определи калорийность."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            logger.info(f"Making API request to {self.base_url}chat/completions")
            response = await self._make_request(
                "POST",
                f"{self.base_url}chat/completions",
                headers=headers,
                json=payload
            )
            
            logger.info(f"API response received: {response is not None}")
            if response:
                logger.info(f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
            
            if response and "choices" in response:
                result = response["choices"][0]["message"]["content"]
                logger.info(f"Analysis result length: {len(result) if result else 0}")
                # Сохраняем в кэш
                self._set_cache(cache_key, result)
                return result
            
            logger.error("No valid response from API")
            return None
            
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error analyzing image: {e}")
            return None
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error analyzing image: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error analyzing image: {e}")
            return None
    
    async def analyze_text(self, text: str) -> Optional[str]:
        """Анализирует текстовое описание еды (ПРОМПТ 3)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "Qwen/Qwen2.5-VL-72B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": """Ты эксперт по анализу еды и подсчету калорий. 
                        Проанализируй описание еды и предоставь информацию в следующем формате:
                        
                        🍽️ Анализ блюда:

                        Название: [название блюда]
                        Вес: [общий вес блюда]г
                        Калорийность: [ОБЩАЯ калорийность для всего количества] ккал

                        📊 БЖУ на 100г:
                        • Белки: [количество]г
                        • Жиры: [количество]г  
                        • Углеводы: [количество]г

                        📈 Общее БЖУ в блюде:
                        • Белки: [общее количество]г
                        • Жиры: [общее количество]г
                        • Углеводы: [общее количество]г
                        
                        КРИТИЧЕСКИ ВАЖНО - СТАНДАРТНЫЕ КАЛОРИЙНОСТИ:
                        • Мясо жаренное: 250 ккал/100г
                        • Яблоки: 50 ккал/100г  
                        • Халва: 450 ккал/100г
                        
                        МАТЕМАТИЧЕСКИЕ ПРАВИЛА (ОБЯЗАТЕЛЬНО!):
                        1. Сначала определи калорийность на 100г для данного продукта
                        2. Затем рассчитай ОБЩУЮ калорийность: (общий_вес_в_граммах ÷ 100) × калорийность_на_100г
                        3. НИКОГДА не округляй промежуточные результаты!
                        4. ОДИНАКОВЫЙ вес = ОДИНАКОВАЯ калорийность!
                        
                        ОБЯЗАТЕЛЬНЫЕ ПРИМЕРЫ:
                        • "мясо 500г" = 500г, 1250 ккал (500÷100×250=1250)
                        • "мясо пол кило" = 500г, 1250 ккал (500÷100×250=1250)
                        • "мясо пол килограма" = 500г, 1250 ккал (500÷100×250=1250)
                        • "мясо 1 кг" = 1000г, 2500 ккал (1000÷100×250=2500)
                        • "мясо 2 кг" = 2000г, 5000 ккал (2000÷100×250=5000) 
                        • "мясо 3 кг" = 3000г, 7500 ккал (3000÷100×250=7500)
                        
                        • "яблоко" = 150г, 75 ккал (150÷100×50=75)
                        • "яблоко 2 шт" = 300г, 150 ккал (300÷100×50=150)
                        • "яблоко 3 шт" = 450г, 225 ккал (450÷100×50=225)
                        
                        КОНТРОЛЬНАЯ ФОРМУЛА:
                        Общая калорийность = (вес_в_г ÷ 100) × калорийность_на_100г
                        
                        НЕ добавляй никаких дополнительных пояснений, расчетов или объяснений!
                        НЕ используй обратные слеши (\\) в числах!
                        
                        Пример правильного формата:
                        • Белки: 0,3г (не 03г)
                        • Жиры: 2,5г (не 25г)
                        • Углеводы: 13,8г (не 138г)
                        
                        Используй запятую как десятичный разделитель: 0,3г вместо 0.3г"""
                    },
                    {
                        "role": "user",
                        "content": f"Проанализируй это описание еды и определи калорийность: {text}"
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            response = await self._make_request(
                "POST",
                f"{self.base_url}chat/completions",
                headers=headers,
                json=payload
            )
            
            if response and "choices" in response:
                return response["choices"][0]["message"]["content"]
            
            return None
            
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error analyzing text: {e}")
            return None
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error analyzing text: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error analyzing text: {e}")
            return None
    
    async def analyze_photo_supplement(self, photo_analysis: str, user_text: str) -> Optional[str]:
        """Дополняет анализ фото текстом пользователя (ПРОМПТ 2)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Создаем промпт для дополнения анализа
            combined_prompt = f"""Исходный анализ фото:
{photo_analysis}

Дополнительная информация от пользователя:
{user_text}

На основе анализа фото и дополнительной информации пользователя, предоставь уточненный анализ в следующем формате:

🍽️ Анализ блюда:

Название: [название блюда]
Вес: [общий вес блюда]г
Калорийность: [ОБЩАЯ калорийность для всего количества] ккал

📊 БЖУ на 100г:
• Белки: [количество]г
• Жиры: [количество]г  
• Углеводы: [количество]г

📈 Общее БЖУ в блюде:
• Белки: [общее количество]г
• Жиры: [общее количество]г
• Углеводы: [общее количество]г

КРИТИЧЕСКИ ВАЖНО - СТАНДАРТНЫЕ КАЛОРИЙНОСТИ:
• Мясо жаренное: 250 ккал/100г
• Яблоки: 50 ккал/100г  
• Халва: 450 ккал/100г

МАТЕМАТИЧЕСКИЕ ПРАВИЛА (ОБЯЗАТЕЛЬНО!):
1. Сначала определи калорийность на 100г для данного продукта
2. Затем рассчитай ОБЩУЮ калорийность: (общий_вес_в_граммах ÷ 100) × калорийность_на_100г
3. НИКОГДА не округляй промежуточные результаты!
4. ОДИНАКОВЫЙ вес = ОДИНАКОВАЯ калорийность!

ОБЯЗАТЕЛЬНЫЕ ПРИМЕРЫ:
• "яблоко 3 кг" = 3000г, 1500 ккал (3000÷100×50=1500)
• "яблоки 3 кг" = 3000г, 1500 ккал (3000÷100×50=1500)

КОНТРОЛЬНАЯ ФОРМУЛА:
Общая калорийность = (вес_в_г ÷ 100) × калорийность_на_100г

НЕ добавляй никаких дополнительных пояснений, расчетов или объяснений!
НЕ используй обратные слеши (\\) в числах!

Пример правильного формата:
• Белки: 0,3г (не 03г)
• Жиры: 2,5г (не 25г)
• Углеводы: 13,8г (не 138г)

Используй запятую как десятичный разделитель: 0,3г вместо 0.3г

Учти дополнительную информацию пользователя для более точного определения веса, ингредиентов и способа приготовления."""
            
            payload = {
                "model": "Qwen/Qwen2.5-VL-72B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты эксперт по анализу еды и подсчету калорий. Используй анализ фото как основу и дополняй его информацией от пользователя для более точного результата."
                    },
                    {
                        "role": "user",
                        "content": combined_prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            response = await self._make_request(
                "POST",
                f"{self.base_url}chat/completions",
                headers=headers,
                json=payload
            )
            
            if response and "choices" in response:
                return response["choices"][0]["message"]["content"]
            
            return None
            
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error analyzing photo supplement: {e}")
            return None
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error analyzing photo supplement: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error analyzing photo supplement: {e}")
            return None

    async def analyze_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Анализирует голосовое описание еды через распознавание речи"""
        try:
            from voice_handler import voice_handler
            
            logger.info("Starting voice analysis with speech recognition")
            
            # Используем VoiceHandler для распознавания речи
            recognized_text = await voice_handler.process_voice_message(update, context)
            
            if not recognized_text:
                logger.warning("Voice recognition failed - no text returned")
                return None
            
            logger.info(f"Voice recognition successful: '{recognized_text[:100]}...'")
            
            # Теперь анализируем распознанный текст через обычный API
            return await self.analyze_text(recognized_text)
            
        except ImportError as e:
            logger.error(f"Import error in voice analysis: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error analyzing voice: {e}")
            return None
    
    async def analyze_photo_with_text(self, image_data: bytes, user_text: str) -> Optional[str]:
        """Анализирует фото + текст пользователя (ПРОМПТ 1 + ПРОМПТ 2)"""
        try:
            # Сначала анализируем фото (ПРОМПТ 1)
            photo_analysis = await self.analyze_image(image_data)
            if not photo_analysis:
                logger.error("Failed to analyze photo")
                return None
            
            # Затем дополняем анализ текстом (ПРОМПТ 2)
            supplemented_analysis = await self.analyze_photo_supplement(photo_analysis, user_text)
            if not supplemented_analysis:
                logger.error("Failed to supplement photo analysis with text")
                return None
            
            logger.info(f"Photo+text analysis successful, result length: {len(supplemented_analysis)}")
            return supplemented_analysis
                        
        except Exception as e:
            logger.error(f"Unexpected error analyzing photo with text: {e}")
            return None

# Глобальный экземпляр клиента
api_client = APIClient()
