"""
Обработчик голосовых сообщений для распознавания речи
Использует внешний сервис для конвертации голоса в текст
"""
import asyncio
import aiohttp
import aiofiles
import tempfile
import os
from typing import Optional
from logging_config import get_logger
from config import API_KEYS, MAX_AUDIO_SIZE, OPENAI_WHISPER_MODEL
from telegram import Update
from telegram.ext import ContextTypes

logger = get_logger(__name__)

class VoiceHandler:
    """Класс для обработки голосовых сообщений"""
    
    def __init__(self):
        # Используем OpenAI API для распознавания речи (Whisper)
        self.openai_api_key = API_KEYS.get("openai_api")
        self.openai_base_url = "https://api.openai.com/v1"
        
        # Fallback на другие сервисы если OpenAI недоступен
        self.assemblyai_api_key = API_KEYS.get("assemblyai_api")
        self.assemblyai_base_url = "https://api.assemblyai.com/v2"
    
    async def process_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Обрабатывает голосовое сообщение и возвращает распознанный текст"""
        try:
            user = update.effective_user
            voice = update.message.voice
            
            logger.info(f"Processing voice message from user {user.id}, duration: {voice.duration}s")
            
            # Проверяем длительность голосового сообщения
            if voice.duration > 60:  # Максимум 60 секунд
                logger.warning(f"Voice message too long: {voice.duration}s")
                return None
            
            # Получаем файл голосового сообщения
            voice_file = await context.bot.get_file(voice.file_id)
            
            # Скачиваем аудиофайл
            async with aiohttp.ClientSession() as session:
                async with session.get(voice_file.file_path) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download voice file: {response.status}")
                        return None
                    
                    audio_data = await response.read()
                    
                    # Проверяем размер файла
                    if len(audio_data) > MAX_AUDIO_SIZE:
                        logger.error(f"Audio file too large: {len(audio_data)} bytes")
                        return None
                    
                    # Распознаем речь
                    return await self._transcribe_audio(audio_data)
                    
        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            return None
    
    async def _transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Распознает речь из аудиоданных используя различные сервисы"""
        try:
            # Пробуем OpenAI Whisper API
            if self.openai_api_key:
                result = await self._transcribe_with_openai(audio_data)
                if result:
                    return result
                logger.warning("OpenAI transcription failed, trying fallback")
            
            # Fallback на AssemblyAI
            if self.assemblyai_api_key:
                result = await self._transcribe_with_assemblyai(audio_data)
                if result:
                    return result
                logger.warning("AssemblyAI transcription failed")
            
            # Если все сервисы недоступны, используем простой fallback
            logger.error("All transcription services failed")
            return self._fallback_transcription()
                        
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    async def _transcribe_with_openai(self, audio_data: bytes) -> Optional[str]:
        """Распознает речь используя OpenAI Whisper API"""
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Используем OpenAI API для транскрипции
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}"
                }
                
                with open(temp_file_path, 'rb') as audio_file:
                    files = {
                        'file': ('audio.ogg', audio_file, 'audio/ogg')
                    }
                    data = {
                        'model': OPENAI_WHISPER_MODEL,
                        'language': 'ru',  # Указываем русский язык
                        'response_format': 'text'
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.openai_base_url}/audio/transcriptions",
                            headers=headers,
                            data=data,
                            files=files
                        ) as response:
                            if response.status == 200:
                                transcribed_text = await response.text()
                                logger.info(f"OpenAI transcription successful: '{transcribed_text[:100]}...'")
                                return transcribed_text.strip()
                            else:
                                error_text = await response.text()
                                logger.error(f"OpenAI API error: {response.status} - {error_text}")
                                return None
            finally:
                # Удаляем временный файл
                try:
                    os.unlink(temp_file_path)
                except OSError as e:
                    logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error with OpenAI transcription: {e}")
            return None
    
    async def _transcribe_with_assemblyai(self, audio_data: bytes) -> Optional[str]:
        """Распознает речь используя AssemblyAI API"""
        try:
            headers = {
                "authorization": self.assemblyai_api_key
            }
            
            # Загружаем аудио
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.assemblyai_base_url}/upload",
                    headers=headers,
                    data=audio_data
                ) as response:
                    if response.status != 200:
                        logger.error(f"AssemblyAI upload error: {response.status}")
                        return None
                    
                    upload_result = await response.json()
                    upload_url = upload_result.get('upload_url')
                    
                    if not upload_url:
                        logger.error("No upload URL from AssemblyAI")
                        return None
                
                # Запускаем транскрипцию
                transcript_data = {
                    "audio_url": upload_url,
                    "language_code": "ru"  # Русский язык
                }
                
                async with session.post(
                    f"{self.assemblyai_base_url}/transcript",
                    headers=headers,
                    json=transcript_data
                ) as response:
                    if response.status != 200:
                        logger.error(f"AssemblyAI transcript error: {response.status}")
                        return None
                    
                    transcript_result = await response.json()
                    transcript_id = transcript_result.get('id')
                    
                    if not transcript_id:
                        logger.error("No transcript ID from AssemblyAI")
                        return None
                
                # Ждем завершения транскрипции
                max_attempts = 30  # Максимум 30 попыток (30 секунд)
                for attempt in range(max_attempts):
                    await asyncio.sleep(1)  # Ждем 1 секунду
                    
                    async with session.get(
                        f"{self.assemblyai_base_url}/transcript/{transcript_id}",
                        headers=headers
                    ) as response:
                        if response.status != 200:
                            continue
                        
                        result = await response.json()
                        status = result.get('status')
                        
                        if status == 'completed':
                            transcribed_text = result.get('text', '')
                            if transcribed_text:
                                logger.info(f"AssemblyAI transcription successful: '{transcribed_text[:100]}...'")
                                return transcribed_text.strip()
                            else:
                                logger.error("Empty transcription result from AssemblyAI")
                                return None
                        elif status == 'error':
                            logger.error(f"AssemblyAI transcription error: {result.get('error', 'Unknown error')}")
                            return None
                
                logger.error("AssemblyAI transcription timeout")
                return None
                
        except Exception as e:
            logger.error(f"Error with AssemblyAI transcription: {e}")
            return None
    
    def _fallback_transcription(self) -> Optional[str]:
        """Fallback функция когда все сервисы недоступны"""
        logger.warning("Using fallback transcription - no API keys available")
        # Возвращаем специальный маркер, который будет обработан в handle_voice
        return "VOICE_TRANSCRIPTION_UNAVAILABLE"

# Глобальный экземпляр обработчика
voice_handler = VoiceHandler()
