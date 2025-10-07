#!/bin/bash

# Скрипт для отката промптов к предыдущей версии
# Использование: ./restore_prompts.sh

BACKUP_DIR="backup/20251007_170348"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Ошибка: Директория бекапа не найдена: $BACKUP_DIR"
    exit 1
fi

echo "🔄 Восстанавливаю промпты из бекапа..."

# Восстанавливаем файлы
cp "$BACKUP_DIR/api_client.py" ./
cp "$BACKUP_DIR/food_analysis_service.py" services/

echo "✅ Промпты восстановлены из бекапа: $BACKUP_DIR"
echo "📁 Восстановленные файлы:"
echo "   - api_client.py"
echo "   - services/food_analysis_service.py"
echo ""
echo "🔄 Перезапустите бота для применения изменений:"
echo "   pkill -f 'python main.py' && sleep 2 && python main.py"

