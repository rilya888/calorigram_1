import sqlite3
import os
import threading
from logging_config import get_logger
from contextlib import contextmanager
from typing import Optional, Tuple, Any, List, Dict
from performance_optimizations import db_optimizer

from config import DATABASE_PATH

logger = get_logger(__name__)

# Thread-local storage для connection pooling
_local = threading.local()

def get_db_connection_pooled():
    """Получает соединение с базой данных из пула"""
    if not hasattr(_local, 'connection') or _local.connection is None:
        _local.connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        _local.connection.row_factory = sqlite3.Row
        
        _local.connection.execute("PRAGMA foreign_keys = ON;")
        _local.connection.execute("PRAGMA journal_mode = WAL;")
        _local.connection.execute("PRAGMA synchronous = NORMAL;")

        # Применяем оптимизации производительности
        db_optimizer.optimize_queries(_local.connection)
    return _local.connection

def create_database() -> bool:
    """Создает базу данных и таблицы пользователей и приемов пищи"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу пользователей с указанными полями
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    height REAL NOT NULL,
                    weight REAL NOT NULL,
                    activity_level TEXT NOT NULL,
                    daily_calories INTEGER NOT NULL,
                    goal TEXT DEFAULT 'maintain',
                    target_calories INTEGER DEFAULT 0,
                    target_protein REAL DEFAULT 0,
                    target_fat REAL DEFAULT 0,
                    target_carbs REAL DEFAULT 0,
                    subscription_type TEXT DEFAULT 'trial',
                    subscription_expires_at TIMESTAMP NULL,
                    is_premium BOOLEAN DEFAULT 0,
                    timezone TEXT DEFAULT 'Europe/Moscow',
                    reminders_enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создаем таблицу приемов пищи
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS meals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    meal_type TEXT NOT NULL,
                    meal_name TEXT NOT NULL,
                    dish_name TEXT NOT NULL,
                    calories INTEGER NOT NULL,
                    protein REAL DEFAULT 0,
                    fat REAL DEFAULT 0,
                    carbs REAL DEFAULT 0,
                    analysis_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
            ''')
            
            # Создаем таблицу для отслеживания использования функции "Узнать калории"
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calorie_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    check_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
            ''')
            
            # Создаем таблицу для отслеживания истории регистраций
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_registration_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    first_registration_at TIMESTAMP NOT NULL,
                    trial_used BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создаем индексы для быстрого поиска
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_telegram_id ON users(telegram_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_meals_telegram_id ON meals(telegram_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_meals_date ON meals(created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_meals_type ON meals(meal_type)
            ''')
            
            # Дополнительные индексы для оптимизации
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_meals_telegram_date ON meals(telegram_id, created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_calorie_checks_telegram ON calorie_checks(telegram_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_calorie_checks_date ON calorie_checks(created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_type, subscription_expires_at)
            ''')
            
            conn.commit()
        logger.info("Database created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False

@contextmanager
def get_db_connection():
    """Контекстный менеджер для работы с базой данных с улучшенной обработкой ошибок"""
    conn = None
    try:
        # Проверяем существование файла БД
        if not os.path.exists(DATABASE_PATH):
            logger.warning(f"Database file not found at {DATABASE_PATH}, creating new database...")
            if not create_database():
                raise sqlite3.Error("Failed to create database")
        
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")  # Для доступа к колонкам по имени
        
        # Применяем оптимизации производительности
        try:
            db_optimizer.optimize_queries(conn)
        except Exception as e:
            logger.warning(f"Failed to apply database optimizations: {e}")
        
        yield conn
    except sqlite3.OperationalError as e:
        logger.error(f"Database operational error: {e}")
        if conn:
            conn.rollback()
        raise
    except sqlite3.IntegrityError as e:
        logger.error(f"Database integrity error: {e}")
        if conn:
            conn.rollback()
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database connection: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")

def get_user_by_telegram_id(telegram_id: int) -> Optional[Tuple[Any, ...]]:
    """Получает пользователя по telegram_id"""
    try:
        if not isinstance(telegram_id, int) or telegram_id <= 0:
            logger.warning(f"Invalid telegram_id: {telegram_id}")
            return None
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting user by telegram_id {telegram_id}: {e}")
        return None

def get_all_users_for_broadcast() -> List[Tuple[int, str]]:
    """Получает всех пользователей для рассылки"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id, name FROM users ORDER BY created_at DESC")
            rows = cursor.fetchall()
            # Преобразуем Row объекты в кортежи
            return [(row[0], row[1]) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all users for broadcast: {e}")
        return []

def create_user(telegram_id: int, name: str, gender: str, age: int, 
                height: float, weight: float, activity_level: str, 
                daily_calories: int) -> bool:
    """Создает нового пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (telegram_id, name, gender, age, height, weight, activity_level, daily_calories)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (telegram_id, name, gender, age, height, weight, activity_level, daily_calories))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        logger.warning(f"User with telegram_id {telegram_id} already exists")
        return False
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False

def create_user_with_goal(telegram_id: int, name: str, gender: str, age: int, 
                         height: float, weight: float, activity_level: str, 
                         daily_calories: int, goal: str, target_calories: int) -> bool:
    """Создает нового пользователя с целью и целевой нормой калорий"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (telegram_id, name, gender, age, height, weight, activity_level, daily_calories, goal, target_calories)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (telegram_id, name, gender, age, height, weight, activity_level, daily_calories, goal, target_calories))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        logger.warning(f"User with telegram_id {telegram_id} already exists")
        return False
    except Exception as e:
        logger.error(f"Error creating user with goal: {e}")
        return False

def delete_user_by_telegram_id(telegram_id: int) -> bool:
    """Удаляет пользователя по telegram_id"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            deleted_rows = cursor.rowcount
            conn.commit()
            return deleted_rows > 0
    except Exception as e:
        logger.error(f"Error deleting user with telegram_id {telegram_id}: {e}")
        return False

def add_meal(telegram_id: int, meal_type: str, meal_name: str, dish_name: str, 
             calories: int, protein: float = 0.0, fat: float = 0.0, carbs: float = 0.0, 
             analysis_type: str = "unknown") -> bool:
    """Добавляет запись о приеме пищи с БЖУ"""
    try:
        logger.info(f"Adding meal to database: telegram_id={telegram_id}, meal_type={meal_type}, meal_name={meal_name}, dish_name={dish_name}, calories={calories}, protein={protein}, fat={fat}, carbs={carbs}, analysis_type={analysis_type}")
        
        # Проверяем, существует ли пользователь
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            logger.error(f"User {telegram_id} not found in database. Cannot add meal.")
            return False
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO meals (telegram_id, meal_type, meal_name, dish_name, calories, protein, fat, carbs, analysis_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (telegram_id, meal_type, meal_name, dish_name, calories, protein, fat, carbs, analysis_type))
            conn.commit()
            logger.info(f"Meal successfully added to database for user {telegram_id}")
            return True
    except Exception as e:
        logger.error(f"Error adding meal for telegram_id {telegram_id}: {e}")
        return False

def get_user_meals(telegram_id: int, date_from: str = None, date_to: str = None) -> list:
    """Получает приемы пищи пользователя за период"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if date_from and date_to:
                cursor.execute('''
                    SELECT * FROM meals 
                    WHERE telegram_id = ? AND DATE(created_at) BETWEEN ? AND ?
                    ORDER BY created_at DESC
                ''', (telegram_id, date_from, date_to))
            else:
                cursor.execute('''
                    SELECT * FROM meals 
                    WHERE telegram_id = ? 
                    ORDER BY created_at DESC
                ''', (telegram_id,))
            
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting meals for telegram_id {telegram_id}: {e}")
        return []

def get_daily_calories(telegram_id: int, date: str = None) -> dict:
    """Получает статистику калорий за день"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if date:
                cursor.execute('''
                    SELECT 
                        COALESCE(SUM(calories), 0) as total_calories,
                        COUNT(*) as meals_count
                    FROM meals 
                    WHERE telegram_id = ? AND DATE(created_at) = ?
                ''', (telegram_id, date))
            else:
                cursor.execute('''
                    SELECT 
                        COALESCE(SUM(calories), 0) as total_calories,
                        COUNT(*) as meals_count
                    FROM meals 
                    WHERE telegram_id = ? AND DATE(created_at) = DATE('now')
                ''', (telegram_id,))
            
            result = cursor.fetchone()
            return {
                'total_calories': result[0] or 0,
                'meals_count': result[1] or 0
            }
    except Exception as e:
        logger.error(f"Error getting daily calories for telegram_id {telegram_id}: {e}")
        return {
            'total_calories': 0,
            'meals_count': 0
        }

def get_meal_statistics(telegram_id: int, days: int = 7) -> dict:
    """Получает статистику приемов пищи за последние N дней"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    SUM(calories) as daily_calories,
                    COUNT(*) as meals_count
                FROM meals 
                WHERE telegram_id = ? AND created_at >= DATE('now', '-{} days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            '''.format(days), (telegram_id,))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting meal statistics for telegram_id {telegram_id}: {e}")
        return []

def delete_meal(meal_id: int, telegram_id: int) -> bool:
    """Удаляет запись о приеме пищи"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meals WHERE id = ? AND telegram_id = ?", (meal_id, telegram_id))
            deleted_rows = cursor.rowcount
            conn.commit()
            return deleted_rows > 0
    except Exception as e:
        logger.error(f"Error deleting meal {meal_id} for telegram_id {telegram_id}: {e}")
        return False

def get_daily_meals_by_type(telegram_id: int, date: str = None) -> dict:
    """Получает калории и БЖУ по типам приемов пищи за день с суммированием всех блюд"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if date:
                cursor.execute('''
                    SELECT 
                        meal_type,
                        meal_name,
                        SUM(calories) as total_calories,
                        SUM(protein) as total_protein,
                        SUM(fat) as total_fat,
                        SUM(carbs) as total_carbs,
                        GROUP_CONCAT(dish_name, ', ') as dishes
                    FROM meals 
                    WHERE telegram_id = ? AND DATE(created_at) = ?
                    GROUP BY meal_type, meal_name
                    ORDER BY 
                        CASE meal_type
                            WHEN 'meal_breakfast' THEN 1
                            WHEN 'meal_lunch' THEN 2
                            WHEN 'meal_dinner' THEN 3
                            WHEN 'meal_snack' THEN 4
                            ELSE 5
                        END
                ''', (telegram_id, date))
            else:
                cursor.execute('''
                    SELECT 
                        meal_type,
                        meal_name,
                        SUM(calories) as total_calories,
                        SUM(protein) as total_protein,
                        SUM(fat) as total_fat,
                        SUM(carbs) as total_carbs,
                        GROUP_CONCAT(dish_name, ', ') as dishes
                    FROM meals 
                    WHERE telegram_id = ? AND DATE(created_at) = DATE('now')
                    GROUP BY meal_type, meal_name
                    ORDER BY 
                        CASE meal_type
                            WHEN 'meal_breakfast' THEN 1
                            WHEN 'meal_lunch' THEN 2
                            WHEN 'meal_dinner' THEN 3
                            WHEN 'meal_snack' THEN 4
                            ELSE 5
                        END
                ''', (telegram_id,))
            
            results = cursor.fetchall()
            meals_dict = {}
            
            for row in results:
                meal_type = row[0]
                meal_name = row[1]
                calories = row[2]
                protein = row[3] or 0
                fat = row[4] or 0
                carbs = row[5] or 0
                dishes = row[6] or ""
                
                meals_dict[meal_type] = {
                    'name': meal_name,
                    'calories': calories,
                    'protein': protein,
                    'fat': fat,
                    'carbs': carbs,
                    'dishes': dishes
                }
            
            return meals_dict
    except Exception as e:
        logger.error(f"Error getting daily meals by type for telegram_id {telegram_id}: {e}")
        return {}

def is_meal_already_added(telegram_id: int, meal_type: str, date: str = None) -> bool:
    """Проверяет, был ли уже добавлен прием пищи сегодня"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if date:
                cursor.execute('''
                    SELECT COUNT(*) FROM meals 
                    WHERE telegram_id = ? AND meal_type = ? AND DATE(created_at) = ?
                ''', (telegram_id, meal_type, date))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM meals 
                    WHERE telegram_id = ? AND meal_type = ? AND DATE(created_at) = DATE('now')
                ''', (telegram_id, meal_type))
            
            count = cursor.fetchone()[0]
            return count > 0
    except Exception as e:
        logger.error(f"Error checking if meal already added for telegram_id {telegram_id}: {e}")
        return False

def get_weekly_meals_by_type(telegram_id: int) -> dict:
    """Получает калории по дням недели за последние 7 дней"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем данные за последние 7 дней
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    SUM(calories) as total_calories
                FROM meals 
                WHERE telegram_id = ? 
                AND DATE(created_at) >= DATE('now', '-6 days')
                AND DATE(created_at) <= DATE('now')
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at)
            ''', (telegram_id,))
            
            results = cursor.fetchall()
            
            # Создаем словарь с днями недели
            days_names = [
                'Понедельник', 'Вторник', 'Среда', 'Четверг', 
                'Пятница', 'Суббота', 'Воскресенье'
            ]
            
            week_stats = {}
            
            # Инициализируем все дни нулями
            for day in days_names:
                week_stats[day] = 0
            
            # Заполняем данные из базы
            for row in results:
                date_str = row[0]
                calories = row[1]
                
                # Получаем день недели
                cursor.execute('''
                    SELECT strftime('%w', ?)
                ''', (date_str,))
                day_of_week = cursor.fetchone()[0]
                
                # Преобразуем в индекс (0=воскресенье, 1=понедельник, ...)
                day_index = int(day_of_week)
                if day_index == 0:  # Воскресенье
                    day_index = 6
                else:
                    day_index -= 1
                
                if 0 <= day_index < 7:
                    week_stats[days_names[day_index]] = calories
            
            return week_stats
    except Exception as e:
        logger.error(f"Error getting weekly meals by type for telegram_id {telegram_id}: {e}")
        return {}

def delete_today_meals(telegram_id: int) -> bool:
    """Удаляет все приемы пищи за сегодняшний день"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Удаляем все приемы пищи за сегодня
            cursor.execute('''
                DELETE FROM meals 
                WHERE telegram_id = ? AND DATE(created_at) = DATE('now')
            ''', (telegram_id,))
            
            deleted_rows = cursor.rowcount
            conn.commit()
            
            logger.info(f"Deleted {deleted_rows} meals for user {telegram_id} for today")
            return deleted_rows > 0
    except Exception as e:
        logger.error(f"Error deleting today's meals for telegram_id {telegram_id}: {e}")
        return False

def delete_all_user_meals(telegram_id: int) -> bool:
    """Удаляет все приемы пищи пользователя за все время"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Удаляем все приемы пищи пользователя
            cursor.execute('''
                DELETE FROM meals 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            
            deleted_rows = cursor.rowcount
            conn.commit()
            
            logger.info(f"Deleted {deleted_rows} meals for user {telegram_id} for all time")
            return deleted_rows > 0
    except Exception as e:
        logger.error(f"Error deleting all meals for telegram_id {telegram_id}: {e}")
        return False

def get_all_users() -> list:
    """Получает всех пользователей для админки"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT telegram_id, name, gender, age, height, weight, 
                       activity_level, daily_calories, created_at
                FROM users 
                ORDER BY created_at DESC
            ''')
            
            users = cursor.fetchall()
            return users
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

def get_user_count() -> int:
    """Получает общее количество пользователей"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            return count
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        return 0

def get_meals_count() -> int:
    """Получает общее количество записей о приемах пищи"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM meals')
            count = cursor.fetchone()[0]
            return count
    except Exception as e:
        logger.error(f"Error getting meals count: {e}")
        return 0

def get_recent_meals(limit: int = 10) -> list:
    """Получает последние записи о приемах пищи"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.telegram_id, u.name, m.meal_name, m.dish_name, 
                       m.calories, m.analysis_type, m.created_at
                FROM meals m
                LEFT JOIN users u ON m.telegram_id = u.telegram_id
                ORDER BY m.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            meals = cursor.fetchall()
            return meals
    except Exception as e:
        logger.error(f"Error getting recent meals: {e}")
        return []

def get_daily_stats() -> dict:
    """Получает статистику за сегодня"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Количество пользователей, добавивших еду сегодня
            cursor.execute('''
                SELECT COUNT(DISTINCT telegram_id) 
                FROM meals 
                WHERE DATE(created_at) = DATE('now')
            ''')
            active_users = cursor.fetchone()[0]
            
            # Общее количество калорий за сегодня
            cursor.execute('''
                SELECT SUM(calories) 
                FROM meals 
                WHERE DATE(created_at) = DATE('now')
            ''')
            total_calories = cursor.fetchone()[0] or 0
            
            # Количество записей за сегодня
            cursor.execute('''
                SELECT COUNT(*) 
                FROM meals 
                WHERE DATE(created_at) = DATE('now')
            ''')
            meals_today = cursor.fetchone()[0]
            
            return {
                'active_users': active_users,
                'total_calories': total_calories,
                'meals_today': meals_today
            }
    except Exception as e:
        logger.error(f"Error getting daily stats: {e}")
        return {'active_users': 0, 'total_calories': 0, 'meals_today': 0}

def migrate_database() -> bool:
    """Мигрирует существующую базу данных, добавляя новые таблицы"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Проверяем, существует ли таблица meals
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='meals'
            ''')
            
            if not cursor.fetchone():
                # Создаем таблицу приемов пищи
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS meals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    meal_type TEXT NOT NULL,
                    meal_name TEXT NOT NULL,
                    dish_name TEXT NOT NULL,
                    calories INTEGER NOT NULL,
                    protein REAL DEFAULT 0,
                    fat REAL DEFAULT 0,
                    carbs REAL DEFAULT 0,
                    analysis_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
                ''')
                
                # Создаем индексы для новой таблицы
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_meals_telegram_id ON meals(telegram_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_meals_date ON meals(created_at)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_meals_type ON meals(meal_type)
                ''')
                
                conn.commit()
                logger.info("Meals table created successfully")
                return True
            else:
                # Проверяем, есть ли старые колонки
                cursor.execute("PRAGMA table_info(meals)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Проверяем, есть ли колонки protein, fat, carbs
                if 'protein' not in columns or 'fat' not in columns or 'carbs' not in columns:
                    # Добавляем недостающие колонки БЖУ
                    if 'protein' not in columns:
                        cursor.execute('ALTER TABLE meals ADD COLUMN protein REAL DEFAULT 0')
                    if 'fat' not in columns:
                        cursor.execute('ALTER TABLE meals ADD COLUMN fat REAL DEFAULT 0')
                    if 'carbs' not in columns:
                        cursor.execute('ALTER TABLE meals ADD COLUMN carbs REAL DEFAULT 0')
                    
                    conn.commit()
                    logger.info("Meals table migrated successfully - added protein, fat, carbs columns")
                else:
                    logger.info("Meals table already exists and is up to date")
            
            # Проверяем и добавляем поля подписки в таблицу users
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'subscription_type' not in columns:
                logger.info("Adding subscription fields to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN subscription_type TEXT DEFAULT "trial"')
                cursor.execute('ALTER TABLE users ADD COLUMN subscription_expires_at TIMESTAMP NULL')
                cursor.execute('ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT 0')
                
                # Устанавливаем триальный период для существующих пользователей
                cursor.execute('''
                    UPDATE users 
                    SET subscription_expires_at = datetime(created_at, '+1 day')
                    WHERE subscription_type = 'trial' AND subscription_expires_at IS NULL
                ''')
                
                conn.commit()
                logger.info("Added subscription fields to users table")
            else:
                logger.info("Subscription fields already exist in users table")
            
            # Проверяем, существует ли таблица calorie_checks
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='calorie_checks'
            ''')
            
            if not cursor.fetchone():
                # Создаем таблицу для отслеживания использования функции "Узнать калории"
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS calorie_checks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER NOT NULL,
                        check_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                    )
                ''')
                
                conn.commit()
                logger.info("Calorie checks table created successfully")
            else:
                logger.info("Calorie checks table already exists")
            
            # Проверяем и добавляем поля цели и целевой нормы калорий в таблицу users
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'goal' not in columns:
                logger.info("Adding goal field to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN goal TEXT DEFAULT "maintain"')
                conn.commit()
                logger.info("Added goal field to users table")
            else:
                logger.info("Goal field already exists in users table")
            
            if 'target_calories' not in columns:
                logger.info("Adding target_calories field to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN target_calories INTEGER DEFAULT 0')
                conn.commit()
                logger.info("Added target_calories field to users table")
            else:
                logger.info("Target_calories field already exists in users table")
            
            # Проверяем и добавляем поля для напоминаний
            if 'timezone' not in columns:
                logger.info("Adding timezone field to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT "Europe/Moscow"')
                conn.commit()
                logger.info("Added timezone field to users table")
            else:
                logger.info("Timezone field already exists in users table")
            
            if 'reminders_enabled' not in columns:
                logger.info("Adding reminders_enabled field to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN reminders_enabled BOOLEAN DEFAULT 1')
                conn.commit()
                logger.info("Added reminders_enabled field to users table")
            else:
                logger.info("Reminders_enabled field already exists in users table")
            
            # Проверяем, существует ли таблица истории регистраций
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='user_registration_history'
            ''')
            
            if not cursor.fetchone():
                # Создаем таблицу истории регистраций
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_registration_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER NOT NULL,
                        first_registration_at TIMESTAMP NOT NULL,
                        trial_used BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Создаем индекс для быстрого поиска
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_registration_history_telegram_id 
                    ON user_registration_history(telegram_id)
                ''')
                
                conn.commit()
                logger.info("User registration history table created successfully")
            else:
                logger.info("User registration history table already exists")
            
            return True
    except Exception as e:
        logger.error(f"Error migrating database: {e}")
        return False

def check_user_subscription(telegram_id: int) -> dict:
    """Проверяет статус подписки пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT subscription_type, subscription_expires_at, is_premium, created_at
                FROM users 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            
            result = cursor.fetchone()
            if not result:
                return {'is_active': False, 'type': 'none', 'expires_at': None}
            
            subscription_type, expires_at, is_premium, created_at = result
            
            # Если это триальный период
            if subscription_type == 'trial':
                # Проверяем историю регистраций
                history = get_user_registration_history(telegram_id)
                if history and history[3]:  # trial_used = True
                    # Триальный период уже был использован
                    return {'is_active': False, 'type': 'trial_used', 'expires_at': None}
                
                if expires_at:
                    # Проверяем, не истек ли триальный период
                    cursor.execute('''
                        SELECT datetime('now') > ?
                    ''', (expires_at,))
                    is_expired = cursor.fetchone()[0]
                    
                    if is_expired:
                        # Отмечаем триал как использованный
                        mark_trial_as_used(telegram_id)
                        return {'is_active': False, 'type': 'trial_expired', 'expires_at': expires_at}
                    else:
                        return {'is_active': True, 'type': 'trial', 'expires_at': expires_at}
                else:
                    # Если нет даты истечения, проверяем, можно ли дать триал
                    if not history:
                        # Первая регистрация - создаем историю и даем триал
                        create_user_registration_history(telegram_id, created_at)
                        cursor.execute('''
                            UPDATE users 
                            SET subscription_expires_at = datetime(created_at, '+1 day')
                            WHERE telegram_id = ?
                        ''', (telegram_id,))
                        conn.commit()
                        
                        cursor.execute('''
                            SELECT datetime(created_at, '+1 day')
                            FROM users 
                            WHERE telegram_id = ?
                        ''', (telegram_id,))
                        expires_at = cursor.fetchone()[0]
                        
                        return {'is_active': True, 'type': 'trial', 'expires_at': expires_at}
                    else:
                        # Триал уже был использован
                        return {'is_active': False, 'type': 'trial_used', 'expires_at': None}
            
            # Если это премиум подписка
            elif subscription_type == 'premium' and is_premium:
                if expires_at:
                    cursor.execute('''
                        SELECT datetime('now') > ?
                    ''', (expires_at,))
                    is_expired = cursor.fetchone()[0]
                    
                    if is_expired:
                        return {'is_active': False, 'type': 'premium_expired', 'expires_at': expires_at}
                    else:
                        return {'is_active': True, 'type': 'premium', 'expires_at': expires_at}
                else:
                    return {'is_active': True, 'type': 'premium', 'expires_at': None}
            
            return {'is_active': False, 'type': 'none', 'expires_at': None}
            
    except Exception as e:
        logger.error(f"Error checking user subscription: {e}")
        return {'is_active': False, 'type': 'error', 'expires_at': None}

def activate_premium_subscription(telegram_id: int, days: int = 30) -> bool:
    """Активирует премиум подписку для пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Устанавливаем премиум подписку
            cursor.execute('''
                UPDATE users 
                SET subscription_type = 'premium',
                    is_premium = 1,
                    subscription_expires_at = datetime('now', '+{} days')
                WHERE telegram_id = ?
            '''.format(days), (telegram_id,))
            
            conn.commit()
            logger.info(f"Activated premium subscription for user {telegram_id} for {days} days")
            return True
            
    except Exception as e:
        logger.error(f"Error activating premium subscription: {e}")
        return False

def get_daily_calorie_checks_count(telegram_id: int) -> int:
    """Получает количество использований функции 'Узнать калории' за сегодня"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM calorie_checks 
                WHERE telegram_id = ? AND DATE(created_at) = DATE('now')
            ''', (telegram_id,))
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error getting daily calorie checks count: {e}")
        return 0

def add_calorie_check(telegram_id: int, check_type: str) -> bool:
    """Добавляет запись об использовании функции 'Узнать калории'"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO calorie_checks (telegram_id, check_type) 
                VALUES (?, ?)
            ''', (telegram_id, check_type))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error adding calorie check: {e}")
        return False

def reset_daily_calorie_checks() -> bool:
    """Сбрасывает счетчик использований функции 'Узнать калории' для всех пользователей"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Удаляем все записи старше 1 дня
            cursor.execute('''
                DELETE FROM calorie_checks 
                WHERE created_at < DATE('now', '-1 day')
            ''')
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Reset daily calorie checks: deleted {deleted_count} old records")
            return True
    except Exception as e:
        logger.error(f"Error resetting daily calorie checks: {e}")
        return False

def update_user_timezone(telegram_id: int, timezone: str) -> bool:
    """Обновляет часовой пояс пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET timezone = ? 
                WHERE telegram_id = ?
            ''', (timezone, telegram_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating user timezone: {e}")
        return False

def update_user_reminders(telegram_id: int, enabled: bool) -> bool:
    """Обновляет настройки напоминаний пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET reminders_enabled = ? 
                WHERE telegram_id = ?
            ''', (enabled, telegram_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating user reminders: {e}")
        return False

def get_user_reminder_settings(telegram_id: int) -> dict:
    """Получает настройки напоминаний пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timezone, reminders_enabled 
                FROM users 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'timezone': result[0],
                    'reminders_enabled': bool(result[1])
                }
            return {'timezone': 'Europe/Moscow', 'reminders_enabled': True}
    except Exception as e:
        logger.error(f"Error getting user reminder settings: {e}")
        return {'timezone': 'Europe/Moscow', 'reminders_enabled': True}

def get_users_with_reminders_enabled() -> List[Tuple[int, str, str]]:
    """Получает пользователей с включенными напоминаниями"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT telegram_id, name, timezone 
                FROM users 
                WHERE reminders_enabled = 1
            ''')
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting users with reminders enabled: {e}")
        return []

def has_user_added_meal_today(telegram_id: int, meal_type: str) -> bool:
    """Проверяет, добавил ли пользователь прием пищи сегодня"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM meals 
                WHERE telegram_id = ? 
                AND meal_type = ? 
                AND DATE(created_at) = DATE('now')
            ''', (telegram_id, meal_type))
            count = cursor.fetchone()[0]
            return count > 0
    except Exception as e:
        logger.error(f"Error checking if user added meal today: {e}")
        return False

def get_all_users_for_admin() -> List[Tuple[int, str, str, int, float, float, str, int, str]]:
    """Получает всех пользователей для админки с полной информацией"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT telegram_id, name, gender, age, height, weight, 
                       activity_level, daily_calories, created_at
                FROM users 
                ORDER BY created_at DESC
            ''')
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting all users for admin: {e}")
        return []

def get_daily_macros(telegram_id: int, date: str = None) -> Dict[str, float]:
    """Получает БЖУ за день для пользователя"""
    try:
        if date is None:
            date = "DATE('now')"
        else:
            date = f"DATE('{date}')"
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT 
                    COALESCE(SUM(protein), 0) as total_protein,
                    COALESCE(SUM(fat), 0) as total_fat,
                    COALESCE(SUM(carbs), 0) as total_carbs,
                    COALESCE(SUM(calories), 0) as total_calories
                FROM meals 
                WHERE telegram_id = ? 
                AND DATE(created_at) = {date}
            ''', (telegram_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'protein': float(result[0]),
                    'fat': float(result[1]),
                    'carbs': float(result[2]),
                    'calories': int(result[3])
                }
            else:
                return {'protein': 0.0, 'fat': 0.0, 'carbs': 0.0, 'calories': 0}
                
    except Exception as e:
        logger.error(f"Error getting daily macros: {e}")
        return {'protein': 0.0, 'fat': 0.0, 'carbs': 0.0, 'calories': 0}


def get_meals_by_type(telegram_id: int, date: str = None) -> List[Dict[str, Any]]:
    """Получает приемы пищи по типам за день"""
    try:
        if date is None:
            date = "DATE('now')"
        else:
            date = f"DATE('{date}')"
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT 
                    meal_type,
                    meal_name,
                    calories,
                    protein,
                    fat,
                    carbs,
                    created_at
                FROM meals 
                WHERE telegram_id = ? 
                AND DATE(created_at) = {date}
                ORDER BY created_at ASC
            ''', (telegram_id,))
            
            meals = []
            for row in cursor.fetchall():
                meals.append({
                    'meal_type': row[0],
                    'meal_name': row[1],
                    'calories': row[2],
                    'protein': float(row[3]),
                    'fat': float(row[4]),
                    'carbs': float(row[5]),
                    'time': row[6].split(' ')[1][:5] if ' ' in str(row[6]) else ''
                })
            
            return meals
                
    except Exception as e:
        logger.error(f"Error getting meals by type: {e}")
        return []


def update_user_target_macros(telegram_id: int, target_protein: float, target_fat: float, target_carbs: float) -> bool:
    """Обновляет целевые БЖУ пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET target_protein = ?, target_fat = ?, target_carbs = ?
                WHERE telegram_id = ?
            ''', (target_protein, target_fat, target_carbs, telegram_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Updated target macros for user {telegram_id}: protein={target_protein}, fat={target_fat}, carbs={target_carbs}")
                return True
            else:
                logger.warning(f"User {telegram_id} not found for macro update")
                return False
                
    except Exception as e:
        logger.error(f"Error updating target macros for user {telegram_id}: {e}")
        return False


def get_user_target_macros(telegram_id: int) -> Dict[str, float]:
    """Получает целевые БЖУ пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT target_protein, target_fat, target_carbs, target_calories
                FROM users 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'protein': float(result[0]) if result[0] else 0.0,
                    'fat': float(result[1]) if result[1] else 0.0,
                    'carbs': float(result[2]) if result[2] else 0.0,
                    'calories': int(result[3]) if result[3] else 0
                }
            else:
                return {'protein': 0.0, 'fat': 0.0, 'carbs': 0.0, 'calories': 0}
                
    except Exception as e:
        logger.error(f"Error getting target macros for user {telegram_id}: {e}")
        return {'protein': 0.0, 'fat': 0.0, 'carbs': 0.0, 'calories': 0}


def get_user_registration_history(telegram_id: int) -> Optional[Tuple[Any, ...]]:
    """Получает историю регистрации пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_registration_history 
                WHERE telegram_id = ?
                ORDER BY created_at DESC LIMIT 1
            ''', (telegram_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting user registration history: {e}")
        return None

def create_user_registration_history(telegram_id: int, first_registration_at: str) -> bool:
    """Создает запись в истории регистраций"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_registration_history (telegram_id, first_registration_at, trial_used)
                VALUES (?, ?, 0)
            ''', (telegram_id, first_registration_at))
            conn.commit()
            logger.info(f"Created registration history for user {telegram_id}")
            return True
    except Exception as e:
        logger.error(f"Error creating user registration history: {e}")
        return False

def mark_trial_as_used(telegram_id: int) -> bool:
    """Отмечает, что триальный период был использован"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_registration_history 
                SET trial_used = 1 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            conn.commit()
            logger.info(f"Marked trial as used for user {telegram_id}")
            return True
    except Exception as e:
        logger.error(f"Error marking trial as used: {e}")
        return False

# Создаем базу данных при импорте модуля
if not os.path.exists(DATABASE_PATH):
    if not create_database():
        logger.error("Failed to create database")
else:
    # Мигрируем существующую базу данных
    if not migrate_database():
        logger.error("Failed to migrate database")


# === Single-instance DB lock (survives restarts) ===
def ensure_lock_table():
    """Создаёт таблицу locks (если нет)."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS locks (
                    name TEXT PRIMARY KEY,
                    owner TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"ensure_lock_table error: {e}")
        return False

def acquire_db_lock(name: str, owner: str) -> bool:
    """Пытается установить блокировку (уникальная запись). Возвращает True при успехе."""
    ensure_lock_table()
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO locks (name, owner) VALUES (?, ?)", (name, owner))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        logger.warning(f"Lock '{name}' already held")
        return False
    except Exception as e:
        logger.error(f"acquire_db_lock error: {e}")
        return False

def release_db_lock(name: str) -> bool:
    """Снимает блокировку."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM locks WHERE name = ?", (name,))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"release_db_lock error: {e}")
        return False


def ensure_payments_table():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS processed_payments (
                    provider_charge_id TEXT PRIMARY KEY,
                    telegram_id INTEGER,
                    amount INTEGER,
                    currency TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"ensure_payments_table error: {e}")
        return False

def is_payment_processed(provider_charge_id: str) -> bool:
    ensure_payments_table()
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM processed_payments WHERE provider_charge_id = ?", (provider_charge_id,))
        return c.fetchone() is not None

def mark_payment_processed(provider_charge_id: str, telegram_id: int, amount: int, currency: str) -> bool:
    ensure_payments_table()
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO processed_payments (provider_charge_id, telegram_id, amount, currency) VALUES (?, ?, ?, ?)",
                      (provider_charge_id, telegram_id, amount, currency))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        logger.error(f"mark_payment_processed error: {e}")
        return False
