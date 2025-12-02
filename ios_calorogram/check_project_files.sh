#!/bin/bash
echo "🔍 Проверка файлов в проекте Calorigram"
echo "========================================"
echo ""

TOTAL_FILES=$(find Calorigram -name "*.swift" 2>/dev/null | wc -l | tr -d ' ')
echo "📁 Всего Swift файлов в папке Calorigram/: $TOTAL_FILES"
echo ""

echo "📋 Список всех файлов:"
find Calorigram -name "*.swift" 2>/dev/null | sort | nl

echo ""
echo "✅ Ожидается: 34 файла"
if [ "$TOTAL_FILES" -eq 34 ]; then
    echo "✅ Все файлы на месте!"
else
    echo "⚠️  Найдено $TOTAL_FILES файлов, ожидалось 34"
fi
