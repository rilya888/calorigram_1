#!/bin/bash

# Скрипт для создания Xcode проекта через командную строку
# Использует Swift Package Manager и затем конвертирует в Xcode проект

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🚀 Создание Xcode проекта через командную строку"
echo "=================================================="
echo ""

# Проверяем наличие необходимых инструментов
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ xcodebuild не найден"
    exit 1
fi

echo "✅ xcodebuild найден"
echo ""

# Пробуем открыть Swift Package в Xcode для генерации проекта
echo "📦 Используем Swift Package Manager..."
echo ""

# Проверяем Package.swift
if [ ! -f "Package.swift" ]; then
    echo "❌ Package.swift не найден"
    exit 1
fi

echo "✅ Package.swift найден"
echo ""

# Пробуем создать Xcode проект через swift package
echo "🔨 Генерируем Xcode проект из Swift Package..."
swift package generate-xcodeproj 2>&1 || {
    echo "⚠️  swift package generate-xcodeproj не сработал (может быть устаревшим)"
    echo "Пробуем альтернативный метод..."
}

# Альтернативный метод: создаем базовую структуру .xcodeproj
if [ ! -d "Calorigram.xcodeproj" ]; then
    echo "📁 Создаем структуру .xcodeproj вручную..."
    
    mkdir -p Calorigram.xcodeproj/project.xcworkspace/xcshareddata
    mkdir -p Calorigram.xcodeproj/xcshareddata/xcschemes
    
    # Создаем workspace settings
    cat > Calorigram.xcodeproj/project.xcworkspace/contents.xcworkspacedata << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<Workspace
   version = "1.0">
   <FileRef
      location = "self:">
   </FileRef>
</Workspace>
EOF

    echo "✅ Базовая структура создана"
    echo ""
    echo "⚠️  ВНИМАНИЕ: Полный .xcodeproj файл требует ручного создания в Xcode GUI"
    echo "   или использования специальных инструментов (xcodegen, tuist и т.д.)"
    echo ""
    echo "📋 Рекомендуется:"
    echo "   1. Открыть Xcode"
    echo "   2. File → New → Project"
    echo "   3. iOS → App"
    echo "   4. Добавить файлы из папки Calorigram/"
    echo ""
fi

echo "✅ Готово!"

