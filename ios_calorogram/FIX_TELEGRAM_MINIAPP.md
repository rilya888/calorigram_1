# 🔧 Исправление проблемы с Telegram Mini App

## Проблема

Telegram Mini App не работает, ошибка: `column users.email does not exist`

## Причина

Миграция базы данных для iOS авторизации не была применена. В таблице `users` отсутствует колонка `email`.

## Решение

### Быстрый способ через Railway Dashboard:

1. Зайдите на [Railway Dashboard](https://railway.app)
2. Выберите ваш проект
3. Выберите сервис с **PostgreSQL базой данных** (не backend!)
4. Откройте вкладку **"Data"** или **"Query"**
5. Скопируйте и выполните этот SQL:

```sql
-- Добавляем поля email и phone_number
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email VARCHAR(255),
ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20);

-- Создаем индексы
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone_number ON users(phone_number);

-- Делаем telegram_id nullable
ALTER TABLE users ALTER COLUMN telegram_id DROP NOT NULL;

-- Таблица для email/password credentials
CREATE TABLE IF NOT EXISTS user_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_credentials_user_id ON user_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credentials_email ON user_credentials(email);

-- Таблица для SMS кодов
CREATE TABLE IF NOT EXISTS phone_verifications (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    code VARCHAR(6) NOT NULL,
    attempts INTEGER DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_phone_verifications_phone_number ON phone_verifications(phone_number);
CREATE INDEX IF NOT EXISTS idx_phone_verifications_expires_at ON phone_verifications(expires_at);

-- Таблица для Apple Sign In
CREATE TABLE IF NOT EXISTS apple_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    apple_user_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_apple_credentials_user_id ON apple_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_apple_credentials_apple_user_id ON apple_credentials(apple_user_id);
```

6. Нажмите **"Run"** или **"Execute"**

### Проверка

После выполнения SQL проверьте:

1. Перезапустите backend сервис на Railway (если нужно)
2. Попробуйте открыть Telegram Mini App снова
3. Ошибка `column users.email does not exist` должна исчезнуть

## Подробная инструкция

См. файл `backend/RAILWAY_MIGRATION.md` в репозитории для альтернативных способов применения миграции.

---

**После применения миграции Telegram Mini App должен заработать!** ✅

