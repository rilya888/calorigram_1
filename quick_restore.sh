#!/bin/bash

# Быстрый откат промптов
echo "🔄 Быстрый откат промптов..."

# Останавливаем бота
pkill -f "python main.py" 2>/dev/null
sleep 2

# Восстанавливаем из бекапа
cp backup/20251007_170348/api_client.py ./
cp backup/20251007_170348/food_analysis_service.py services/

echo "✅ Промпты откачены к версии 20251007_170348"
echo "🔄 Перезапускаем бота..."

# Запускаем бота
python main.py &

