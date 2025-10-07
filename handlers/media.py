# Auto-generated module for media handlers extracted from bot_functions.py
from ._shared import *  # imports, constants, helpers
from database import add_meal, add_calorie_check
from constants import MAX_IMAGE_SIZE, MAX_AUDIO_SIZE
import bot_functions as bf  # for cross-module handler calls
from handlers.menu import get_main_menu_keyboard_for_user
from services.food_analysis_service import (
    analyze_food_photo_with_text, 
    analyze_food_photo,
    analyze_food_supplement,
    is_valid_analysis,
    remove_explanations_from_analysis,
    extract_macros_from_analysis,
    extract_dish_name_from_analysis,
    clean_markdown_text
)
from logging_config import get_logger
import aiohttp

logger = get_logger(__name__)

__all__ = []

def validate_image_file(file_data: bytes) -> bool:
    """Валидация изображения по содержимому файла"""
    try:
        # Проверяем размер файла
        if len(file_data) > MAX_IMAGE_SIZE:
            return False
        
        # Проверяем магические байты для определения типа файла
        if file_data.startswith(b'\xff\xd8\xff'):  # JPEG
            return True
        elif file_data.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            return True
        elif file_data.startswith(b'RIFF') and b'WEBP' in file_data[:12]:  # WebP
            return True
        elif file_data.startswith(b'GIF87a') or file_data.startswith(b'GIF89a'):  # GIF
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error validating image file: {e}")
        return False

async def handle_check_photo_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Фото + Текст' для проверки калорий"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем подписку и лимит использований
    access_info = check_subscription_access(user.id)
    if not access_info['has_access']:
        daily_checks = get_daily_calorie_checks_count(user.id)
        if daily_checks >= 3:
            limit_msg = f"❌ **Лимит использований исчерпан**\n\n"
            limit_msg += f"Вы использовали функцию 'Узнать калории' {daily_checks}/3 раз сегодня.\n\n"
            limit_msg += f"⏰ **Счетчик сбрасывается в полночь**\n\n"
            limit_msg += f"💡 **Для неограниченного использования оформите подписку:**\n"
            limit_msg += f"• 1 день - 50 ⭐\n"
            limit_msg += f"• 7 дней - 200 ⭐\n"
            limit_msg += f"• 30 дней - 500 ⭐\n"
            limit_msg += f"• 90 дней - 1200 ⭐\n"
            limit_msg += f"• 365 дней - 4000 ⭐\n\n"
            limit_msg += f"💎 Безопасно • Мгновенно • Без комиссий"
            
            await query.edit_message_text(
                limit_msg,
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
            return
    
    # Устанавливаем состояние ожидания фото
    context.user_data['waiting_for_check_photo_text'] = True
    
    await query.edit_message_text(
        "📷📝 **Комбинированный анализ блюда**\n\n"
        "**Шаг 1:** Отправьте фото блюда\n\n"
        "**Шаг 2:** После анализа фото отправьте текстовое описание с уточнениями:\n"
        "• Размер порции (\"большая тарелка\", \"2 куска\", \"примерно 300г\")\n"
        "• Дополнительные ингредиенты (\"с добавлением сыра\", \"без масла\")\n"
        "• Способ приготовления (\"домашний рецепт\", \"жареное\")\n\n"
        "**Примеры уточнений:**\n"
        "• \"Большая порция, диаметр 30см, с добавлением моцареллы\"\n"
        "• \"2 куска, домашний рецепт, без масла\"\n"
        "• \"Примерно 250г, с двойной порцией мяса\"\n\n"
        "⚠️ **Для более точного расчета на фото должны присутствовать якорные объекты:**\n"
        "• Вилка, ложка, рука, монета или другие объекты для масштаба\n\n"
        "ℹ️ **Результат будет показан, но НЕ сохранится в вашу статистику**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_check_photo_text_callback')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий"""
    is_for_adding = context.user_data.get('waiting_for_photo', False)
    is_for_checking = context.user_data.get('waiting_for_check_photo', False)
    is_for_photo_text = context.user_data.get('waiting_for_photo_text', False)
    is_for_check_photo_text = context.user_data.get('waiting_for_check_photo_text', False)
    
    if not (is_for_adding or is_for_checking or is_for_photo_text or is_for_check_photo_text):
        # Если пользователь отправил фото без выбора действия, показываем подсказку
        await update.message.reply_text(
            "📷 **Фото получено!**\n\n"
            "Но сначала выберите, что вы хотите сделать:\n\n"
            "🍽️ **Добавить блюдо** - для сохранения в статистику\n"
            "🔍 **Узнать калории** - для быстрой проверки\n\n"
            "Используйте кнопки в главном меню.",
            reply_markup=get_main_menu_keyboard_for_user(update),
            parse_mode='Markdown'
        )
        return
    
    user = update.effective_user
    photo = update.message.photo[-1]  # Берем фото в наилучшем качестве
    
    # Сбрасываем состояние ожидания
    context.user_data['waiting_for_photo'] = False
    context.user_data['waiting_for_check_photo'] = False
    context.user_data['waiting_for_photo_text'] = False
    context.user_data['waiting_for_check_photo_text'] = False
    
    # Сбрасываем флаги дополнения анализа для нового фото
    context.user_data.pop('analysis_supplemented', None)
    context.user_data.pop('check_analysis_supplemented', None)
    
    # Отправляем сообщение о начале обработки
    processing_msg = await update.message.reply_text(
        "🔄 **Обрабатываю фотографию...**\n\n"
        "Анализирую изображение с помощью ИИ модели...",
        parse_mode='Markdown'
    )
    
    try:
        # Получаем файл фотографии
        file = await context.bot.get_file(photo.file_id)
        file_url = file.file_path
        
        logger.info(f"Downloading photo from: {file_url}")
        
        # Скачиваем изображение асинхронно с исправленными SSL настройками
        import aiohttp
        import ssl
        
        # Создаем SSL контекст с мягкими настройками
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            if file_url.startswith('https://'):
                url = file_url
            else:
                url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_url}"
            
            async with session.get(url) as response:
                logger.info(f"Photo download response: {response.status}")
                
                if response.status != 200:
                    logger.error(f"Failed to download photo: {response.status}")
                    await processing_msg.edit_text(
                        f"❌ Ошибка при загрузке фотографии\n\n"
                        f"Код ошибки: {response.status}\n"
                        f"URL: {url}\n"
                        f"Попробуйте отправить фото еще раз или используйте команду /addphoto"
                    )
                    return
                
                # Проверяем размер файла
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > MAX_IMAGE_SIZE:
                    await processing_msg.edit_text(
                        f"❌ **Файл слишком большой**\n\n"
                        f"Размер фотографии превышает {MAX_IMAGE_SIZE // (1024 * 1024)}MB. Пожалуйста, отправьте фото меньшего размера.",
                        reply_markup=get_main_menu_keyboard_for_user(update),
                        parse_mode='Markdown'
                    )
                    return
                
                # Читаем содержимое файла
                image_content = await response.read()
                
                # Проверяем размер после загрузки
                if len(image_content) > MAX_IMAGE_SIZE:
                    await processing_msg.edit_text(
                        f"❌ **Файл слишком большой**\n\n"
                        f"Размер фотографии превышает {MAX_IMAGE_SIZE // (1024 * 1024)}MB. Пожалуйста, отправьте фото меньшего размера.",
                        reply_markup=get_main_menu_keyboard_for_user(update),
                        parse_mode='Markdown'
                    )
                    return
                
                # Проверяем тип файла
                if not validate_image_file(image_content):
                    await processing_msg.edit_text(
                        "❌ **Неподдерживаемый формат файла**\n\n"
                        "Пожалуйста, отправьте изображение в формате JPEG, PNG или WebP.",
                        reply_markup=get_main_menu_keyboard_for_user(update),
                        parse_mode='Markdown'
                    )
                    return
        
        # Отправляем запрос к языковой модели
        logger.info("Starting food photo analysis...")
        analysis_result = await analyze_food_photo(image_content)
        logger.info(f"Analysis result: {analysis_result is not None}")
        
        if analysis_result:
            logger.info(f"Analysis result length: {len(analysis_result)}")
            logger.info(f"Analysis result preview: {analysis_result[:200]}...")
        
        # Получаем информацию о выбранном приеме пищи
        selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
        
        # Проверяем валидность анализа
        is_valid = is_valid_analysis(analysis_result) if analysis_result else False
        logger.info(f"Analysis is valid: {is_valid}")
        
        if analysis_result and is_valid:
            # Удаляем пояснения из анализа
            analysis_result = remove_explanations_from_analysis(analysis_result)
            
            # Парсим результат анализа для извлечения БЖУ
            calories, protein, fat, carbs = extract_macros_from_analysis(analysis_result)
            dish_name = extract_dish_name_from_analysis(analysis_result) or "Блюдо по фото"
            
            # Проверяем комбинированный режим
            if is_for_photo_text or is_for_check_photo_text:
                # Сохраняем результат анализа фото для последующего объединения с текстом
                context.user_data['photo_analysis_result'] = analysis_result
                context.user_data['photo_dish_name'] = dish_name
                context.user_data['photo_calories'] = calories
                
                # Устанавливаем состояние ожидания текста
                if is_for_photo_text:
                    context.user_data['waiting_for_text_after_photo'] = True
                else:
                    context.user_data['waiting_for_check_text_after_photo'] = True
                
                await processing_msg.edit_text(
                    "📷 **Фото проанализировано!**\n\n"
                    "Теперь отправьте текстовое описание с уточнениями:\n"
                    "• Размер порции\n"
                    "• Дополнительные ингредиенты\n"
                    "• Способ приготовления\n\n"
                    "**Пример:** \"Большая порция, диаметр 30см, с добавлением моцареллы\"",
                    parse_mode='Markdown'
                )
                return
            
            # Проверяем режим - добавление или проверка калорий
            is_check_mode = context.user_data.get('check_mode', False)
            
            if is_check_mode:
                # Режим проверки калорий - показываем результат с кнопками подтверждения
                # Сохраняем данные анализа для подтверждения
                context.user_data['original_analysis'] = analysis_result
                context.user_data['original_calories'] = calories
                context.user_data['original_dish_name'] = dish_name
                context.user_data['waiting_for_photo_confirmation'] = True
                context.user_data['check_mode'] = True
                
                cleaned_result = clean_markdown_text(analysis_result)
                result_text = f"🔍 **Анализ калорий**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ будут сохранены в статистику**"
                
                await processing_msg.edit_text(
                    result_text, 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_check_analysis")],
                        [InlineKeyboardButton("✏️ Дополнить", callback_data="add_to_check_analysis")],
                        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                    ]), 
                    parse_mode='Markdown'
                )
            else:
                # Режим добавления блюда - показываем результат с кнопками подтверждения
                # Сохраняем данные анализа для подтверждения
                context.user_data['original_analysis'] = analysis_result
                context.user_data['original_calories'] = calories
                context.user_data['original_dish_name'] = dish_name
                context.user_data['waiting_for_photo_confirmation'] = True
                context.user_data['save_mode'] = True
                
                meal_info = f"**🍽️ {selected_meal}**\n\n{analysis_result}"
                cleaned_meal_info = clean_markdown_text(meal_info)
                
                await processing_msg.edit_text(
                    cleaned_meal_info, 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_analysis")],
                        [InlineKeyboardButton("✏️ Дополнить", callback_data="add_to_analysis")],
                        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                    ]), 
                    parse_mode='Markdown'
                )
        elif analysis_result:
            # ИИ вернул результат, но не смог определить калории
            logger.warning(f"Analysis returned but is not valid. Result: {analysis_result[:200]}...")
            await processing_msg.edit_text(
                "❌ **Анализ не удался**\n\n"
                "ИИ не смог определить калорийность блюда на фотографии.\n\n"
                "**Возможные причины:**\n"
                "• На фото нет еды или еда не видна\n"
                "• Слишком темное или размытое изображение\n"
                "• Отсутствуют якорные объекты для масштаба\n\n"
                "**Рекомендации:**\n"
                "• Убедитесь, что на фото четко видна еда\n"
                "• Добавьте вилку, ложку или руку для масштаба\n"
                "• Сделайте фото при хорошем освещении\n\n"
                "Попробуйте отправить другое фото или используйте команду /addtext для текстового описания.",
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
        else:
            # ИИ не вернул результат
            logger.error("No analysis result returned from API")
            await processing_msg.edit_text(
                "❌ **Ошибка анализа**\n\n"
                "Не удалось проанализировать фотографию. Возможные причины:\n"
                "• Проблемы с подключением к серверу\n"
                "• Неподдерживаемый формат изображения\n"
                "• Слишком большой размер файла\n\n"
                "Попробуйте отправить другое фото или используйте команду /addtext для текстового описания.",
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка\n\n"
            "Не удалось обработать фотографию. Попробуйте позже или используйте команду /addphoto снова.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )

__all__.append('handle_photo')

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик голосовых сообщений"""
    is_for_adding = context.user_data.get('waiting_for_voice', False)
    is_for_checking = context.user_data.get('waiting_for_check_voice', False)
    
    if not (is_for_adding or is_for_checking):
        return
    
    user = update.effective_user
    voice = update.message.voice
    
    # Сбрасываем состояние ожидания
    context.user_data['waiting_for_voice'] = False
    context.user_data['waiting_for_check_voice'] = False
    
    # Отправляем сообщение о начале обработки
    processing_msg = await update.message.reply_text(
        "🔄 **Обрабатываю голосовое сообщение...**\n\n"
        "Преобразую речь в текст и анализирую с помощью ИИ...",
        parse_mode='Markdown'
    )
    
    try:
        logger.info(f"Processing voice message from user {user.id}, duration: {voice.duration}s")
        
        # Используем новый API клиент для анализа голоса
        async with api_client:
            analysis_result = await api_client.analyze_voice(update, context)
            
        # Сохраняем распознанный текст в контексте для последующего использования
        if analysis_result and 'recognized_text' in str(analysis_result):
            # Если анализ содержит распознанный текст, извлекаем его
            context.user_data['recognized_text'] = analysis_result
        else:
            context.user_data['recognized_text'] = 'Голосовое сообщение'
        
        if not analysis_result:
            await processing_msg.edit_text(
                "❌ Ошибка распознавания речи\n\n"
                "Не удалось распознать голосовое сообщение. Попробуйте:\n"
                "• Говорить четче и медленнее\n"
                "• Убедиться, что микрофон работает\n"
                "• Использовать команду /addtext для текстового описания\n\n"
                "Попробуйте команду /addvoice снова."
            )
            return
        
        # Проверяем, доступно ли распознавание речи
        if analysis_result == "VOICE_TRANSCRIPTION_UNAVAILABLE":
            await processing_msg.edit_text(
                "🎤 **Распознавание речи временно недоступно**\n\n"
                "Для работы с голосовыми сообщениями необходимо настроить API ключи для распознавания речи.\n\n"
                "**Альтернативы:**\n"
                "• Используйте команду /addtext для текстового описания\n"
                "• Используйте команду /addphoto для анализа фотографий\n"
                "• Отправьте текстовое описание блюда\n\n"
                "**Пример текстового описания:**\n"
                "• \"Большая тарелка борща с мясом и сметаной\"\n"
                "• \"Два куска пиццы Маргарита среднего размера\"",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Текстовый анализ", callback_data="analyze_text")],
                    [InlineKeyboardButton("📷 Анализ фото", callback_data="analyze_photo")],
                    [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
                ]),
                parse_mode='Markdown'
            )
            return
        
        if analysis_result and is_valid_analysis(analysis_result):
            # Удаляем пояснения из анализа
            analysis_result = remove_explanations_from_analysis(analysis_result)
            
            # Парсим результат анализа для извлечения БЖУ
            calories, protein, fat, carbs = extract_macros_from_analysis(analysis_result)
            dish_name = extract_dish_name_from_analysis(analysis_result) or "Голосовое сообщение"
            
            # Проверяем режим - добавление или проверка калорий
            is_check_mode = context.user_data.get('check_mode', False)
            
            if is_check_mode:
                # Режим проверки калорий - только показываем результат
                # Записываем использование функции
                add_calorie_check(user.id, 'voice')
                
                cleaned_result = clean_markdown_text(analysis_result)
                result_text = f"🔍 **Анализ калорий**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ сохранены в статистику**"
                
                await processing_msg.edit_text(
                    result_text, 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
                    ]), 
                    parse_mode='Markdown'
                )
                # Сбрасываем режим проверки
                context.user_data['check_mode'] = False
            else:
                # Режим добавления блюда - сохраняем в базу
                try:
                    meal_type = context.user_data.get('selected_meal', 'meal_breakfast')
                    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
                    
                    # Извлекаем БЖУ из анализа
                    calories_from_analysis, protein, fat, carbs = extract_macros_from_analysis(analysis_result)
                    
                    # Сохраняем в базу данных
                    success = add_meal(
                        telegram_id=user.id,
                        meal_type=meal_type,
                        meal_name=selected_meal,
                        dish_name=dish_name,
                        calories=calories,
                        protein=protein,
                        fat=fat,
                        carbs=carbs,
                        analysis_type="voice"
                    )
                    
                    if success:
                        logger.info(f"Meal saved successfully for user {user.id}")
                        # Добавляем информацию о распознанном тексте
                        cleaned_result = clean_markdown_text(analysis_result)
                        # Получаем распознанный текст из контекста или используем заглушку
                        transcription_result = context.user_data.get('recognized_text', 'Голосовое сообщение')
                        result_with_transcription = f"**🎤 Распознанный текст:** {transcription_result}\n\n{cleaned_result}"
                        await processing_msg.edit_text(result_with_transcription, reply_markup=get_analysis_result_keyboard(), parse_mode='Markdown')
                    else:
                        logger.warning(f"Failed to save meal for user {user.id}")
                        await processing_msg.edit_text(
                            "❌ Ошибка сохранения\n\n"
                            "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                            reply_markup=get_main_menu_keyboard_for_user(update)
                        )
                    
                except Exception as e:
                    logger.error(f"Error saving meal to database: {e}")
                    await processing_msg.edit_text(
                        "❌ Ошибка сохранения\n\n"
                        "Не удалось сохранить данные о приеме пищи. Попробуйте еще раз.",
                        reply_markup=get_main_menu_keyboard_for_user(update)
                )
        elif analysis_result:
            # ИИ вернул результат, но не смог определить калории
            transcription_result = context.user_data.get('recognized_text', 'Голосовое сообщение')
            await processing_msg.edit_text(
                f"**🎤 Распознанный текст:** {transcription_result}\n\n"
                "❌ **Анализ не удался**\n\n"
                "ИИ не смог определить калорийность блюда по описанию.\n\n"
                "**Возможные причины:**\n"
                "• Описание слишком краткое или неясное\n"
                "• Не указан размер порции\n"
                "• Отсутствуют основные ингредиенты\n\n"
                "**Рекомендации:**\n"
                "• Укажите точные ингредиенты и их количество\n"
                "• Добавьте размер порции (например, 'большая тарелка', '2 куска')\n"
                "• Опишите способ приготовления\n\n"
                "Попробуйте дать более подробное описание или используйте команду /addphoto для анализа фото.",
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
        else:
            transcription_result = context.user_data.get('recognized_text', 'Голосовое сообщение')
            await processing_msg.edit_text(
                f"**🎤 Распознанный текст:** {transcription_result}\n\n"
                "❌ **Ошибка анализа**\n\n"
                "Не удалось проанализировать описание блюда. Попробуйте:\n"
                "• Указать более подробное описание\n"
                "• Включить размер порции\n"
                "• Перечислить основные ингредиенты\n\n"
                "Попробуйте команду /addvoice снова.",
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка\n\n"
            "Не удалось обработать голосовое сообщение. Попробуйте позже или используйте команду /addvoice снова.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )

__all__.append('handle_voice')

async def handle_check_photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Анализ по фото' для проверки калорий"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем подписку и лимит использований
    access_info = check_subscription_access(user.id)
    if not access_info['has_access']:
        daily_checks = get_daily_calorie_checks_count(user.id)
        if daily_checks >= 3:
            limit_msg = f"❌ **Лимит использований исчерпан**\n\n"
            limit_msg += f"Вы использовали функцию 'Узнать калории' {daily_checks}/3 раз сегодня.\n\n"
            limit_msg += f"⏰ **Счетчик сбрасывается в полночь**\n\n"
            limit_msg += f"💡 **Для неограниченного использования оформите подписку:**\n"
            limit_msg += f"• 1 день - 50 ⭐\n"
            limit_msg += f"• 7 дней - 200 ⭐\n"
            limit_msg += f"• 30 дней - 500 ⭐\n"
            limit_msg += f"• 90 дней - 1200 ⭐\n"
            limit_msg += f"• 365 дней - 4000 ⭐\n\n"
            limit_msg += f"💎 Безопасно • Мгновенно • Без комиссий"
            
            await query.edit_message_text(
                limit_msg,
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
            return
    
    await query.message.reply_text(
        "📷 **Анализ по фото**\n\n"
        "Отправьте фотографию еды для анализа калорий.\n\n"
        "ℹ️ **Результат будет показан, но НЕ сохранится в статистику**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]),
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние ожидания фото для проверки
    context.user_data['waiting_for_check_photo'] = True
    context.user_data['check_mode'] = True

__all__.append('handle_check_photo_callback')

async def handle_check_voice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Анализ по голосу' для проверки калорий"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Проверяем подписку и лимит использований
    access_info = check_subscription_access(user.id)
    if not access_info['has_access']:
        daily_checks = get_daily_calorie_checks_count(user.id)
        if daily_checks >= 3:
            limit_msg = f"❌ **Лимит использований исчерпан**\n\n"
            limit_msg += f"Вы использовали функцию 'Узнать калории' {daily_checks}/3 раз сегодня.\n\n"
            limit_msg += f"⏰ **Счетчик сбрасывается в полночь**\n\n"
            limit_msg += f"💡 **Для неограниченного использования оформите подписку:**\n"
            limit_msg += f"• 1 день - 50 ⭐\n"
            limit_msg += f"• 7 дней - 200 ⭐\n"
            limit_msg += f"• 30 дней - 500 ⭐\n"
            limit_msg += f"• 90 дней - 1200 ⭐\n"
            limit_msg += f"• 365 дней - 4000 ⭐\n\n"
            limit_msg += f"💎 Безопасно • Мгновенно • Без комиссий"
            
            await query.edit_message_text(
                limit_msg,
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
            return
    
    await query.message.reply_text(
        "🎤 **Анализ по голосу**\n\n"
        "Отправьте голосовое сообщение с описанием блюда для анализа калорий.\n\n"
        "ℹ️ **Результат будет показан, но НЕ сохранится в статистику**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_from_meal_selection")]
        ]),
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние ожидания голоса для проверки
    context.user_data['waiting_for_check_voice'] = True
    context.user_data['check_mode'] = True

__all__.append('handle_check_voice_callback')

async def handle_analyze_photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Анализ по фото'"""
    query = update.callback_query
    await query.answer()
    
    # Устанавливаем состояние ожидания фото
    context.user_data['waiting_for_photo'] = True
    
    # Получаем информацию о выбранном приеме пищи
    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
    
    await query.edit_message_text(
        f"📸 **Анализ фотографии еды - {selected_meal}**\n\n"
        "Пришлите мне фото блюда, калорийность которого вы хотите оценить.\n\n"
        "⚠️ **Для более точного расчета на фото должны присутствовать якорные объекты:**\n"
        "• Вилка\n"
        "• Ложка\n"
        "• Рука\n"
        "• Монета\n"
        "• Другие объекты для масштаба\n\n"
        "Модель проанализирует фото и вернет:\n"
        "• Название блюда\n"
        "• Ориентировочный вес\n"
        "• Калорийность\n"
        "• Раскладку по БЖУ",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_analysis")],
            [InlineKeyboardButton("🔙 Назад к приемам пищи", callback_data="add_dish")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_analyze_photo_callback')

async def handle_analyze_voice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Анализ по голосовому'"""
    query = update.callback_query
    await query.answer()
    
    # Устанавливаем состояние ожидания голосового сообщения
    context.user_data['waiting_for_voice'] = True
    
    # Получаем информацию о выбранном приеме пищи
    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
    
    await query.edit_message_text(
        f"🎤 **Анализ голосового описания блюда - {selected_meal}**\n\n"
        "Отправьте голосовое сообщение с описанием блюда, калорийность которого вы хотите оценить.\n\n"
        "**Примеры описаний:**\n"
        "• \"Большая тарелка борща с мясом и сметаной\"\n"
        "• \"Два куска пиццы Маргарита среднего размера\"\n"
        "• \"Салат Цезарь с курицей и сыром пармезан\"\n"
        "• \"Порция жареной картошки с луком\"\n\n"
        "**Укажите в голосовом сообщении:**\n"
        "• Название блюда\n"
        "• Примерный размер порции\n"
        "• Основные ингредиенты\n\n"
        "Модель проанализирует голосовое сообщение и вернет:\n"
        "• Название блюда\n"
        "• Ориентировочный вес\n"
        "• Калорийность\n"
        "• Раскладку по БЖУ",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_analysis")],
            [InlineKeyboardButton("🔙 Назад к приемам пищи", callback_data="add_dish")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_analyze_voice_callback')

async def handle_analyze_photo_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Фото + Текст' для добавления блюда"""
    query = update.callback_query
    await query.answer()
    
    # Устанавливаем состояние ожидания фото
    context.user_data['waiting_for_photo_text'] = True
    
    # Получаем информацию о выбранном приеме пищи
    selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
    
    await query.edit_message_text(
        f"📷📝 **Комбинированный анализ блюда - {selected_meal}**\n\n"
        "**Шаг 1:** Отправьте фото блюда\n\n"
        "**Шаг 2:** После анализа фото отправьте текстовое описание с уточнениями:\n"
        "• Размер порции (\"большая тарелка\", \"2 куска\", \"примерно 300г\")\n"
        "• Дополнительные ингредиенты (\"с добавлением сыра\", \"без масла\")\n"
        "• Способ приготовления (\"домашний рецепт\", \"жареное\")\n\n"
        "**Примеры уточнений:**\n"
        "• \"Большая порция, диаметр 30см, с добавлением моцареллы\"\n"
        "• \"2 куска, домашний рецепт, без масла\"\n"
        "• \"Примерно 250г, с двойной порцией мяса\"\n\n"
        "⚠️ **Для более точного расчета на фото должны присутствовать якорные объекты:**\n"
        "• Вилка, ложка, рука, монета или другие объекты для масштаба\n\n"
        "Модель проанализирует и фото, и текст для максимально точного результата!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_analysis")],
            [InlineKeyboardButton("🔙 Назад к приемам пищи", callback_data="add_dish")]
        ]),
        parse_mode='Markdown'
    )

__all__.append('handle_analyze_photo_text_callback')

async def handle_photo_with_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает сообщения с фото + текстом для уточненного анализа"""
    user = update.effective_user
    message = update.message
    
    try:
        # Получаем фото и текст
        photo = message.photo[-1]  # Берем самое большое фото
        caption = message.caption or ""
        
        if not caption.strip():
            # Если нет текста, обрабатываем как обычное фото
            await handle_photo(update, context)
            return
        
        logger.info(f"Processing photo with text from user {user.id}: '{caption[:50]}...'")
        
        # Отправляем сообщение о начале обработки
        processing_msg = await message.reply_text(
            "🔍 **Анализирую фото + текст...**\n\n"
            f"📝 Ваш текст: {caption}\n\n"
            "⏳ Пожалуйста, подождите...",
            parse_mode='Markdown'
        )
        
        # Скачиваем фото
        photo_file = await context.bot.get_file(photo.file_id)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_file.file_path) as response:
                if response.status != 200:
                    await processing_msg.edit_text(
                        "❌ **Ошибка загрузки фото**\n\n"
                        "Не удалось загрузить фотографию. Попробуйте еще раз.",
                        reply_markup=get_main_menu_keyboard_for_user(update),
                        parse_mode='Markdown'
                    )
                    return
                
                image_content = await response.read()
                
                # Проверяем размер файла
                if len(image_content) > MAX_IMAGE_SIZE:
                    await processing_msg.edit_text(
                        f"❌ **Файл слишком большой**\n\n"
                        f"Размер фотографии превышает {MAX_IMAGE_SIZE // (1024 * 1024)}MB. Пожалуйста, отправьте фото меньшего размера.",
                        reply_markup=get_main_menu_keyboard_for_user(update),
                        parse_mode='Markdown'
                    )
                    return
                
                # Проверяем тип файла
                if not validate_image_file(image_content):
                    await processing_msg.edit_text(
                        "❌ **Неподдерживаемый формат файла**\n\n"
                        "Пожалуйста, отправьте изображение в формате JPEG, PNG или WebP.",
                        reply_markup=get_main_menu_keyboard_for_user(update),
                        parse_mode='Markdown'
                    )
                    return
        
        # Анализируем фото + текст (ПРОМПТ 1 + ПРОМПТ 2)
        logger.info("Starting photo+text analysis...")
        
        # Сначала анализируем фото (ПРОМПТ 1)
        photo_analysis = await analyze_food_photo(image_content)
        if not photo_analysis:
            await processing_msg.edit_text(
                "❌ **Ошибка анализа фото**\n\n"
                "Не удалось проанализировать фотографию. Попробуйте другое фото.",
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
            return
        
        # Затем дополняем анализ текстом (ПРОМПТ 2)
        analysis_result = await analyze_food_supplement(photo_analysis, caption)
        logger.info(f"Photo+text analysis result: {analysis_result is not None}")
        
        # Сохраняем промежуточный результат для возможного дальнейшего дополнения
        context.user_data['photo_analysis_for_supplement'] = photo_analysis
        
        if analysis_result:
            logger.info(f"Analysis result length: {len(analysis_result)}")
            logger.info(f"Analysis result preview: {analysis_result[:200]}...")
        
        # Получаем информацию о выбранном приеме пищи
        selected_meal = context.user_data.get('selected_meal_name', 'Прием пищи')
        
        # Проверяем валидность анализа
        is_valid = is_valid_analysis(analysis_result) if analysis_result else False
        logger.info(f"Analysis is valid: {is_valid}")
        
        if is_valid:
            # Удаляем пояснения из анализа
            analysis_result = remove_explanations_from_analysis(analysis_result)
            
            # Парсим результат анализа для извлечения БЖУ
            calories, protein, fat, carbs = extract_macros_from_analysis(analysis_result)
            dish_name = extract_dish_name_from_analysis(analysis_result) or caption[:50]
            
            # Проверяем режим - добавление или проверка калорий
            is_check_mode = context.user_data.get('check_mode', False)
            
            if is_check_mode:
                # Режим проверки калорий - показываем результат с кнопками подтверждения
                add_calorie_check(user.id, 'photo_text')
                
                # Сохраняем данные анализа для подтверждения
                context.user_data['original_analysis'] = analysis_result
                context.user_data['original_calories'] = calories
                context.user_data['original_dish_name'] = dish_name
                context.user_data['waiting_for_photo_text_confirmation'] = True
                context.user_data['check_mode'] = True
                
                cleaned_result = clean_markdown_text(analysis_result)
                result_text = f"🔍 **Анализ калорий (фото + текст)**\n\n{cleaned_result}\n\nℹ️ **Данные НЕ будут сохранены в статистику**"
                
                await processing_msg.edit_text(
                    result_text, 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_photo_text_check_analysis")],
                        [InlineKeyboardButton("✏️ Дополнить", callback_data="add_to_photo_text_check_analysis")],
                        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                    ]), 
                    parse_mode='Markdown'
                )
            else:
                # Режим добавления блюда - показываем результат с кнопками подтверждения
                # Сохраняем данные анализа для подтверждения
                context.user_data['original_analysis'] = analysis_result
                context.user_data['original_calories'] = calories
                context.user_data['original_dish_name'] = dish_name
                context.user_data['waiting_for_photo_text_confirmation'] = True
                context.user_data['save_mode'] = True
                
                meal_info = f"**🍽️ {selected_meal}**\n\n{analysis_result}"
                cleaned_meal_info = clean_markdown_text(meal_info)
                
                await processing_msg.edit_text(
                    cleaned_meal_info, 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Все верно?", callback_data="confirm_photo_text_analysis")],
                        [InlineKeyboardButton("✏️ Дополнить", callback_data="add_to_photo_text_analysis")],
                        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_analysis")]
                    ]), 
                    parse_mode='Markdown'
                )
        elif analysis_result:
            # ИИ вернул результат, но не смог определить калории
            await processing_msg.edit_text(
                f"**📝 Ваш текст:** {caption}\n\n"
                "❌ **Анализ не удался**\n\n"
                "ИИ не смог определить калорийность блюда по фото и описанию.\n\n"
                "**Возможные причины:**\n"
                "• Фото нечеткое или плохого качества\n"
                "• Описание слишком краткое или неясное\n"
                "• Не указан размер порции\n"
                "• Отсутствуют основные ингредиенты\n\n"
                "**Рекомендации:**\n"
                "• Укажите точные ингредиенты и их количество\n"
                "• Добавьте размер порции (например, 'большая тарелка', '2 куска')\n"
                "• Опишите способ приготовления\n\n"
                "Попробуйте дать более подробное описание или используйте команду /addphoto для анализа только фото.",
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
        else:
            await processing_msg.edit_text(
                f"**📝 Ваш текст:** {caption}\n\n"
                "❌ **Ошибка анализа**\n\n"
                "Не удалось проанализировать фото и описание блюда. Попробуйте:\n"
                "• Указать более подробное описание\n"
                "• Включить размер порции\n"
                "• Перечислить основные ингредиенты\n\n"
                "Попробуйте команду /addphoto снова.",
                reply_markup=get_main_menu_keyboard_for_user(update),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in handle_photo_with_text: {e}")
        await message.reply_text(
            "❌ Произошла ошибка\n\n"
            "Не удалось обработать фото с текстом. Попробуйте позже или используйте команду /addphoto снова.",
            reply_markup=get_main_menu_keyboard_for_user(update)
        )

__all__.append('handle_photo_with_text')

