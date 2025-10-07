# 🚀 Деплой Calorigram Bot на Railway

## 📋 Предварительные требования

1. **Аккаунт Railway** - зарегистрируйтесь на [railway.app](https://railway.app)
2. **GitHub репозиторий** - код уже загружен в [calorigram_1](https://github.com/rilya888/calorigram_1.git)
3. **Telegram Bot Token** - получите у [@BotFather](https://t.me/BotFather)
4. **Nebius AI API Key** - получите на [nebius.ai](https://nebius.ai)

## 🚀 Пошаговая инструкция деплоя

### 1. Подключение к Railway

1. Войдите в [Railway Dashboard](https://railway.app/dashboard)
2. Нажмите **"New Project"**
3. Выберите **"Deploy from GitHub repo"**
4. Найдите и выберите репозиторий `rilya888/calorigram_1`
5. Нажмите **"Deploy Now"**

### 2. Настройка переменных окружения

В настройках проекта Railway добавьте следующие переменные:

```env
BOT_TOKEN=your_telegram_bot_token_here
NEBUIS_API_KEY=your_nebius_api_key_here
BASE_URL=https://api.studio.nebius.ai/v1/
DATABASE_PATH=users.db
ADMIN_IDS=160308091
TEST_MODE=False
API_TIMEOUT=30
MAX_RETRIES=3
MAX_IMAGE_SIZE=10485760
MAX_AUDIO_SIZE=20971520
```

**Как добавить переменные:**
1. В проекте Railway перейдите в **"Variables"**
2. Нажмите **"New Variable"**
3. Добавьте каждую переменную по отдельности

### 3. Настройка домена

1. В настройках проекта перейдите в **"Settings"**
2. В разделе **"Domains"** нажмите **"Generate Domain"**
3. Скопируйте сгенерированный домен

### 4. Настройка веб-хука (опционально)

Если хотите использовать webhook вместо polling:

1. В настройках проекта найдите **"Public Networking"**
2. Включите **"Public Networking"**
3. Скопируйте URL домена
4. Обновите webhook в коде бота

### 5. Мониторинг

1. Перейдите в **"Deployments"** для просмотра логов
2. Проверьте статус деплоя
3. Убедитесь, что все переменные окружения установлены

## 🔧 Конфигурация для Railway

### Procfile
```
web: python main.py
```

### railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### runtime.txt
```
python-3.11.0
```

## 📊 Мониторинг и логи

### Просмотр логов
1. В Railway Dashboard перейдите в ваш проект
2. Выберите **"Deployments"**
3. Нажмите на последний деплой
4. Перейдите в **"Logs"** для просмотра логов в реальном времени

### Проверка статуса
- ✅ **Deployed** - бот успешно развернут
- ❌ **Failed** - ошибка деплоя (проверьте логи)
- 🔄 **Building** - процесс деплоя в процессе

## 🐛 Устранение неполадок

### Частые проблемы:

1. **Ошибка "Module not found"**
   - Проверьте, что все зависимости в `requirements.txt`
   - Убедитесь, что используется правильная версия Python

2. **Ошибка "Environment variable not found"**
   - Проверьте, что все переменные окружения установлены
   - Убедитесь в правильности названий переменных

3. **Ошибка "Database connection failed"**
   - Railway автоматически создает базу данных
   - Проверьте путь к базе данных в переменных

4. **Бот не отвечает**
   - Проверьте правильность BOT_TOKEN
   - Убедитесь, что бот не запущен локально одновременно

### Полезные команды для отладки:

```bash
# Проверка переменных окружения
railway variables

# Просмотр логов
railway logs

# Подключение к контейнеру
railway shell
```

## 🔄 Обновление бота

1. Внесите изменения в код
2. Зафиксируйте изменения в Git:
   ```bash
   git add .
   git commit -m "Update: описание изменений"
   git push origin main
   ```
3. Railway автоматически развернет обновление

## 📈 Масштабирование

Railway автоматически масштабирует приложение в зависимости от нагрузки. Для увеличения ресурсов:

1. Перейдите в настройки проекта
2. Выберите **"Settings"** → **"Resources"**
3. Увеличьте лимиты CPU и памяти

## 💰 Стоимость

- **Hobby Plan** - бесплатно (до 500 часов в месяц)
- **Pro Plan** - $5/месяц за проект
- **Team Plan** - $20/месяц за пользователя

## 📞 Поддержка

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **GitHub Issues**: [github.com/rilya888/calorigram_1/issues](https://github.com/rilya888/calorigram_1/issues)

## ✅ Чек-лист деплоя

- [ ] Репозиторий подключен к Railway
- [ ] Все переменные окружения установлены
- [ ] Домен сгенерирован
- [ ] Деплой успешно завершен
- [ ] Бот отвечает на команды
- [ ] Логи не содержат ошибок
- [ ] База данных создана
- [ ] Админ-панель работает

---

**🎉 Поздравляем! Ваш Calorigram Bot успешно развернут на Railway!**
