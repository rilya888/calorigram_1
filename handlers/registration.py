"""
Модуль для обработки регистрации пользователей
"""
import logging
from typing import Optional, Tuple, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_db_connection
from constants import (
    GENDERS, MIN_AGE, MAX_AGE, MIN_HEIGHT, MAX_HEIGHT, 
    MIN_WEIGHT, MAX_WEIGHT, ACTIVITY_LEVELS
)
import utils
from logging_config import get_logger

logger = get_logger(__name__)


# ==================== VALIDATION FUNCTIONS ====================

def validate_user_input(telegram_id: int, name: str, gender: str, age: int, 
                       height: float, weight: float, activity_level: str) -> Tuple[bool, str]:
    """Валидирует входные данные пользователя"""
    try:
        # Проверяем telegram_id
        if not utils.validate_telegram_id(telegram_id):
            return False, "Неверный Telegram ID"
        
        # Проверяем имя
        if not name or len(name.strip()) < 2 or len(name.strip()) > 50:
            return False, "Имя должно содержать от 2 до 50 символов"
        
        # Проверяем пол
        if gender not in GENDERS:
            return False, "Неверный пол"
        
        # Проверяем возраст
        if not isinstance(age, int) or age < MIN_AGE or age > MAX_AGE:
            return False, f"Возраст должен быть от {MIN_AGE} до {MAX_AGE} лет"
        
        # Проверяем рост
        if not isinstance(height, (int, float)) or height < MIN_HEIGHT or height > MAX_HEIGHT:
            return False, f"Рост должен быть от {MIN_HEIGHT} до {MAX_HEIGHT} см"
        
        # Проверяем вес
        if not isinstance(weight, (int, float)) or weight < MIN_WEIGHT or weight > MAX_WEIGHT:
            return False, f"Вес должен быть от {MIN_WEIGHT} до {MAX_WEIGHT} кг"
        
        # Проверяем уровень активности
        if activity_level not in ACTIVITY_LEVELS:
            return False, "Неверный уровень активности"
        
        return True, "OK"
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Error validating user input: {e}")
        return False, "Ошибка валидации данных"
    except Exception as e:
        logger.error(f"Unexpected error validating user input: {e}")
        return False, "Ошибка валидации данных"


def validate_age(age: str) -> Optional[int]:
    """Валидирует возраст"""
    try:
        age_int = int(age)
        return age_int if MIN_AGE <= age_int <= MAX_AGE else None
    except (ValueError, TypeError):
        return None


def validate_height(height: str) -> Optional[float]:
    """Валидирует рост"""
    try:
        height_float = float(height.replace(',', '.'))
        return height_float if MIN_HEIGHT <= height_float <= MAX_HEIGHT else None
    except (ValueError, TypeError):
        return None


def validate_weight(weight: str) -> Optional[float]:
    """Валидирует вес"""
    try:
        weight_float = float(weight.replace(',', '.'))
        return weight_float if MIN_WEIGHT <= weight_float <= MAX_WEIGHT else None
    except (ValueError, TypeError):
        return None


def check_user_registration(user_id: int) -> Optional[Tuple[Any, ...]]:
    """Проверяет, зарегистрирован ли пользователь"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
        return cursor.fetchone()


def calculate_daily_calories(age, height, weight, gender: str, activity_level: str) -> int:
    """Рассчитывает суточную норму калорий по формуле Миффлин-Сен Жеор"""
    try:
        # Преобразуем данные в нужные типы
        age = int(age)
        height = float(height)
        weight = float(weight)
        
        logger.info(f"Calculating calories for: age={age}, height={height}, weight={weight}, gender={gender}, activity={activity_level}")
        
        # Формула Миффлин-Сен Жеор (более точная)
        if gender == 'Мужской':
            # BMR для мужчин = (10 * weight) + (6.25 * height) - (5 * age) + 5
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:  # Женский
            # BMR для женщин = (10 * weight) + (6.25 * height) - (5 * age) - 161
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        
        # Коэффициенты активности
        multiplier = ACTIVITY_LEVELS.get(activity_level, 1.55)
        daily_calories = int(bmr * multiplier)
        
        logger.info(f"Calculated BMR: {bmr}, multiplier: {multiplier}, daily_calories: {daily_calories}")
        
        return daily_calories
        
    except Exception as e:
        logger.error(f"Error calculating daily calories: {e}")
        return 2000  # Значение по умолчанию


def calculate_target_calories(daily_calories: int, goal: str) -> int:
    """Рассчитывает целевые калории на основе цели пользователя"""
    if goal == 'lose_weight':
        return int(daily_calories * 0.8)  # Дефицит 20%
    elif goal == 'gain_weight':
        return int(daily_calories * 1.2)  # Профицит 20%
    else:  # maintain - Держать себя в форме
        return daily_calories


# ==================== COMMAND HANDLERS ====================

async def send_not_registered_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет сообщение незарегистрированному пользователю"""
    await update.message.reply_text(
        "Вы не зарегистрированы! Используйте /start для регистрации."
    )


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /register"""
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if existing_user:
            await update.message.reply_text("Вы уже зарегистрированы! Используйте /profile для просмотра данных.")
            return
        
        # Сохраняем состояние регистрации
        context.user_data['registration_step'] = 'name'
        context.user_data['user_data'] = {'telegram_id': user.id}
        
        await update.message.reply_text(
            "Давайте зарегистрируем вас в системе!\n\n"
            "Введите ваше имя:"
        )
    except Exception as e:
        logger.error(f"Error in register_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при проверке регистрации. Попробуйте позже."
        )


async def handle_text_input_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Обрабатывает текстовый ввод для регистрации
    
    Returns:
        bool: True если сообщение было обработано, False если нет
    """
    # Обработка регистрации
    if 'registration_step' not in context.user_data:
        return False
    
    text = update.message.text
    step = context.user_data['registration_step']
    user_data = context.user_data['user_data']
    
    if step == 'name':
        user_data['name'] = text
        context.user_data['registration_step'] = 'gender'
        
        keyboard = [
            [InlineKeyboardButton("👨 Мужской", callback_data="gender_male")],
            [InlineKeyboardButton("👩 Женский", callback_data="gender_female")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите ваш пол:",
            reply_markup=reply_markup
        )
        return True
        
    elif step == 'age':
        age = validate_age(text)
        if age is None:
            await update.message.reply_text(f"Пожалуйста, введите корректный возраст ({MIN_AGE}-{MAX_AGE}):")
            return True
        user_data['age'] = age
        context.user_data['registration_step'] = 'height'
        await update.message.reply_text("Введите ваш рост в см:")
        return True
            
    elif step == 'height':
        height = validate_height(text)
        if height is None:
            await update.message.reply_text(f"Пожалуйста, введите корректный рост ({MIN_HEIGHT}-{MAX_HEIGHT} см):")
            return True
        user_data['height'] = height
        context.user_data['registration_step'] = 'weight'
        await update.message.reply_text("Введите ваш вес в кг:")
        return True
            
    elif step == 'weight':
        weight = validate_weight(text)
        if weight is None:
            await update.message.reply_text(f"Пожалуйста, введите корректный вес ({MIN_WEIGHT}-{MAX_WEIGHT} кг):")
            return True
        user_data['weight'] = weight
        context.user_data['registration_step'] = 'activity'
        
        keyboard = [
            [InlineKeyboardButton("🛌 Минимальная", callback_data="activity_minimal")],
            [InlineKeyboardButton("🏃 Легкая", callback_data="activity_light")],
            [InlineKeyboardButton("💪 Умеренная", callback_data="activity_moderate")],
            [InlineKeyboardButton("🔥 Высокая", callback_data="activity_high")],
            [InlineKeyboardButton("⚡ Очень высокая", callback_data="activity_very_high")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите ваш уровень активности:",
            reply_markup=reply_markup
        )
        return True
    
    return False


# ==================== CALLBACK HANDLERS ====================

async def handle_register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопки регистрации"""
    query = update.callback_query
    user = update.effective_user
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        existing_user = check_user_registration(user.id)
        
        if existing_user:
            await query.message.reply_text(
                "Вы уже зарегистрированы! Используйте /profile для просмотра данных."
            )
            return
            
        # Сохраняем состояние регистрации
        context.user_data['registration_step'] = 'name'
        context.user_data['user_data'] = {'telegram_id': user.id}
        
        await query.message.reply_text(
            "Давайте зарегистрируем вас в системе!\n\n"
            "Введите ваше имя:"
        )
        
    except Exception as e:
        logger.error(f"Error in register callback: {e}")
        await query.message.reply_text(
            "❌ Произошла ошибка при проверке регистрации. Попробуйте позже."
        )


async def handle_gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора пола"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('gender_'):
        # Проверяем, есть ли данные пользователя
        if 'user_data' not in context.user_data:
            await query.message.reply_text(
                "❌ Ошибка: данные регистрации не найдены.\n"
                "Пожалуйста, начните регистрацию заново с помощью /register"
            )
            return
            
        user_data = context.user_data['user_data']
        
        if query.data == 'gender_male':
            user_data['gender'] = 'Мужской'
        elif query.data == 'gender_female':
            user_data['gender'] = 'Женский'
        
        context.user_data['registration_step'] = 'age'
        await query.edit_message_text("Введите ваш возраст:")


async def handle_activity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора уровня активности"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('activity_'):
        # Проверяем, есть ли данные пользователя
        if 'user_data' not in context.user_data:
            await query.message.reply_text(
                "❌ Ошибка: данные регистрации не найдены.\n"
                "Пожалуйста, начните регистрацию заново с помощью /register"
            )
            return
            
        activity_levels = {
            'activity_minimal': 'Минимальная',
            'activity_light': 'Легкая',
            'activity_moderate': 'Умеренная',
            'activity_high': 'Высокая',
            'activity_very_high': 'Очень высокая'
        }
        
        user_data = context.user_data['user_data']
        user_data['activity_level'] = activity_levels[query.data]
        
        # Переходим к выбору цели
        context.user_data['registration_step'] = 'goal'
        
        keyboard = [
            [InlineKeyboardButton("📉 Похудеть", callback_data="goal_lose_weight")],
            [InlineKeyboardButton("⚖️ Держать себя в форме", callback_data="goal_maintain")],
            [InlineKeyboardButton("📈 Набрать вес", callback_data="goal_gain_weight")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎯 **Выберите вашу цель:**\n\n"
            "• **Похудеть** - снижение веса\n"
            "• **Держать себя в форме** - поддержание текущего веса\n"
            "• **Набрать вес** - увеличение веса",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def handle_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора цели"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('goal_'):
        # Проверяем, есть ли данные пользователя
        if 'user_data' not in context.user_data:
            await query.message.reply_text(
                "❌ Ошибка: данные регистрации не найдены.\n"
                "Пожалуйста, начните регистрацию заново с помощью /register"
            )
            return
            
        goals = {
            'goal_lose_weight': 'Похудеть',
            'goal_maintain': 'Держать себя в форме',
            'goal_gain_weight': 'Набрать вес'
        }
        
        user_data = context.user_data['user_data']
        user_data['goal'] = goals[query.data]
        
        # Рассчитываем дневную норму калорий
        daily_calories = calculate_daily_calories(
            user_data['age'],
            user_data['height'],
            user_data['weight'],
            user_data['gender'],
            user_data['activity_level']
        )
        
        target_calories = calculate_target_calories(daily_calories, user_data['goal'])
        
        user_data['daily_calories'] = daily_calories
        user_data['target_calories'] = target_calories
        
        # Валидация всех данных перед сохранением
        is_valid, error_message = validate_user_input(
            user_data['telegram_id'],
            user_data['name'],
            user_data['gender'],
            user_data['age'],
            user_data['height'],
            user_data['weight'],
            user_data['activity_level']
        )
        
        if not is_valid:
            await query.message.reply_text(
                f"❌ Ошибка валидации: {error_message}\n\n"
                "Пожалуйста, начните регистрацию заново с помощью /register"
            )
            # Очищаем данные регистрации
            context.user_data.clear()
            return
        
        # Рассчитываем целевые БЖУ
        from utils.macros_calculator import calculate_daily_macros
        
        target_macros = calculate_daily_macros(
            weight=user_data['weight'],
            activity_level=user_data['activity_level'],
            goal=user_data['goal'],
            target_calories=user_data['target_calories']
        )
        
        # Сохраняем пользователя в БД
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (
                        telegram_id, name, gender, age, height, weight, 
                        activity_level, goal, daily_calories, target_calories,
                        target_protein, target_fat, target_carbs
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_data['telegram_id'],
                    user_data['name'],
                    user_data['gender'],
                    user_data['age'],
                    user_data['height'],
                    user_data['weight'],
                    user_data['activity_level'],
                    user_data['goal'],
                    user_data['daily_calories'],
                    user_data['target_calories'],
                    target_macros['protein'],
                    target_macros['fat'],
                    target_macros['carbs']
                ))
                conn.commit()
            
            success_message = f"""
✅ Регистрация успешно завершена!

📊 Ваши данные:
• Имя: {user_data['name']}
• Пол: {user_data['gender']}
• Возраст: {user_data['age']} лет
• Рост: {user_data['height']} см
• Вес: {user_data['weight']} кг
• Активность: {user_data['activity_level']}
• Цель: {user_data['goal']}

🔥 Суточная норма калорий: {user_data['daily_calories']} ккал
🎯 Целевая норма: {user_data['target_calories']} ккал

🥗 Суточная норма БЖУ:
• Белки: {target_macros['protein']}г ({target_macros['protein_calories']} ккал)
• Жиры: {target_macros['fat']}г ({target_macros['fat_calories']} ккал)
• Углеводы: {target_macros['carbs']}г ({target_macros['carb_calories']} ккал)

Используйте /menu для вызова главного меню
            """
            
            await query.edit_message_text(success_message)
            
            # Очищаем данные регистрации
            context.user_data.clear()
            
            # Получаем данные пользователя из базы данных для приветственного сообщения
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_data['telegram_id'],))
                db_user_data = cursor.fetchone()
            
            if db_user_data:
                # Показываем приветственное сообщение с данными пользователя
                logger.info(f"Calling show_welcome_message_with_data for user {user_data['telegram_id']}")
                from handlers.menu import show_welcome_message_with_data
                await show_welcome_message_with_data(update, context, db_user_data)
            else:
                # Fallback к главному меню
                logger.warning(f"No user data found in DB for user {user_data['telegram_id']}")
                from handlers.menu import show_main_menu
                await show_main_menu(update, context)
            
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
            await query.message.reply_text(
                "❌ Ошибка при сохранении данных. Попробуйте зарегистрироваться снова."
            )
            context.user_data.clear()

