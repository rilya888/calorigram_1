#!/bin/bash
# Script to restore "правильный подсчет" backup

BACKUP_DIR="backup/правильный_подсчет"

echo "🔄 Восстанавливаю промпты из бекапа 'правильный подсчет'..."

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Ошибка: Папка бекапа не найдена: $BACKUP_DIR"
    exit 1
fi

echo "📁 Восстанавливаю файлы из $BACKUP_DIR..."

# Restore api_client.py
if [ -f "$BACKUP_DIR/api_client.py" ]; then
    cp "$BACKUP_DIR/api_client.py" api_client.py
    echo "✅ api_client.py восстановлен"
else
    echo "❌ api_client.py не найден в бекапе"
fi

# Restore services/food_analysis_service.py
if [ -f "$BACKUP_DIR/food_analysis_service.py" ]; then
    cp "$BACKUP_DIR/food_analysis_service.py" services/food_analysis_service.py
    echo "✅ services/food_analysis_service.py восстановлен"
else
    echo "❌ food_analysis_service.py не найден в бекапе"
fi

# Restore handlers/misc.py
if [ -f "$BACKUP_DIR/misc.py" ]; then
    cp "$BACKUP_DIR/misc.py" handlers/misc.py
    echo "✅ handlers/misc.py восстановлен"
else
    echo "❌ misc.py не найден в бекапе"
fi

# Restore handlers/media.py
if [ -f "$BACKUP_DIR/media.py" ]; then
    cp "$BACKUP_DIR/media.py" handlers/media.py
    echo "✅ handlers/media.py восстановлен"
else
    echo "❌ media.py не найден в бекапе"
fi

echo ""
echo "✅ Промпты восстановлены из бекапа: $BACKUP_DIR"
echo "📁 Восстановленные файлы:"
echo "   - api_client.py"
echo "   - services/food_analysis_service.py"
echo "   - handlers/misc.py"
echo "   - handlers/media.py"
echo ""
echo "🔄 Перезапустите бота для применения изменений:"
echo "   pkill -f 'python main.py' && sleep 2 && python main.py"

