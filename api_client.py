"""
Асинхронный клиент для работы с внешними API
"""
import asyncio
import base64
import hashlib
import time
from logging_config import get_logger
from typing import Optional, Dict, Any, Tuple
import aiohttp
import aiofiles
from telegram import Update
from telegram.ext import ContextTypes
from config import API_KEYS, BASE_URL, API_TIMEOUT, MAX_API_RETRIES, MAX_IMAGE_SIZE, MAX_AUDIO_SIZE, OPENAI_MODEL, OPENAI_VISION_MODEL
from performance_optimizations import rate_limiter

logger = get_logger(__name__)

class APIClient:
    """Асинхронный клиент для работы с API"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.api_key = API_KEYS.get("openai_api")
        self.model = OPENAI_MODEL
        self.vision_model = OPENAI_VISION_MODEL
        self.timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Tuple[Any, float]] = {}  # Кэш для результатов
        self.cache_ttl = 300  # TTL кэша в секундах (5 минут)
        self.max_cache_size = 1000  # Максимальный размер кэша
    
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            import ssl
            # Создаем SSL контекст с более мягкими настройками для macOS
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False  # Отключаем проверку hostname для API
            ssl_context.verify_mode = ssl.CERT_NONE  # Временно отключаем проверку сертификатов
            
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
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
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
    
    def _set_cache(self, cache_key: str, result: Any):
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
            except Exception as e:
                logger.error(f"Request error: {e}")
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
                "model": self.vision_model,
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
                        
                        ВАЖНО: Рассчитай калорийность для ВСЕГО видимого количества еды на фото, а не только для 100г!
                        НЕ добавляй никаких дополнительных пояснений, расчетов или объяснений!"""
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
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None
    
    async def analyze_text(self, text: str) -> Optional[str]:
        """Анализирует текстовое описание еды"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
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
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return None
    
    async def analyze_voice(self, update: Optional[Update] = None, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> Optional[str]:
        """Анализирует голосовое описание еды через распознавание речи"""
        try:
            from voice_handler import voice_handler
            
            logger.info("Starting voice analysis with speech recognition")
            
            # Проверяем, что переданы необходимые параметры
            if update is None or context is None:
                logger.error("analyze_voice requires update and context parameters")
                return None
            
            # Используем VoiceHandler для распознавания речи
            recognized_text = await voice_handler.process_voice_message(update, context)
            
            if not recognized_text:
                logger.warning("Voice recognition failed - no text returned")
                return None
            
            logger.info(f"Voice recognition successful: '{recognized_text[:100]}...'")
            
            # Теперь анализируем распознанный текст через обычный API
            return await self.analyze_text(recognized_text)
            
        except Exception as e:
            logger.error(f"Error analyzing voice: {e}")
            return None
    
    async def analyze_photo_with_text(self, image_data: bytes, user_text: str) -> Optional[str]:
        """Анализирует фото + текст пользователя для уточненного анализа"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Сначала анализируем фото
            photo_analysis = await self.analyze_image(image_data)
            if not photo_analysis:
                logger.error("Failed to analyze photo")
                return None
            
            # Создаем объединенный промпт
            combined_prompt = f"""
Исходный анализ фото:
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

Учти дополнительную информацию пользователя для более точного определения веса, ингредиентов и способа приготовления.
"""
            
            payload = {
                "model": self.model,
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
            
            # Создаем SSL контекст
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    f"{self.base_url}chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        analysis_text = result['choices'][0]['message']['content']
                        logger.info(f"Photo+text analysis successful, result length: {len(analysis_text)}")
                        return analysis_text
                    else:
                        error_text = await response.text()
                        logger.error(f"API error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error analyzing photo with text: {e}")
            return None

# Глобальный экземпляр клиента
api_client = APIClient()
