#!/bin/bash
# Скрипт для запуска приложения на симуляторе через командную строку

cd /Users/mac/ios_calorogram

echo "🧹 Очистка проекта..."
xcodebuild -project Calorigram.xcodeproj -scheme Calorigram clean > /dev/null 2>&1

echo "🔨 Сборка для симулятора..."
xcodebuild -project Calorigram.xcodeproj \
  -scheme Calorigram \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  build 2>&1 | grep -E "BUILD SUCCEEDED|BUILD FAILED|error:" | tail -5

APP_PATH=$(find ~/Library/Developer/Xcode/DerivedData/Calorigram-*/Build/Products/Debug-iphonesimulator -name "Calorigram.app" 2>/dev/null | head -1)

if [ -n "$APP_PATH" ]; then
    echo "✅ Приложение собрано: $APP_PATH"
    echo ""
    echo "🚀 Запуск симулятора..."
    xcrun simctl boot "iPhone 17 Pro" 2>/dev/null || echo "Симулятор уже запущен"
    
    echo "📱 Установка приложения..."
    xcrun simctl install booted "$APP_PATH"
    
    echo "▶️  Запуск приложения..."
    xcrun simctl launch booted com.calorigram.Calorigram
    
    echo "✅ Готово! Приложение должно запуститься на симуляторе."
else
    echo "❌ Приложение не найдено. Проверьте ошибки сборки."
fi
