#!/bin/bash
# Скрипт для копирования исполняемого файла в DerivedData

cd /Users/mac/ios_calorogram

# Найти .app в DerivedData
DERIVED_APP=$(find ~/Library/Developer/Xcode/DerivedData/Calorigram-*/Build/Products/Debug-iphonesimulator -name "Calorigram.app" -type d 2>/dev/null | head -1)

# Найти исполняемый файл в build
EXECUTABLE="build/Debug-iphonesimulator/Calorigram.app/Calorigram"

if [ -n "$DERIVED_APP" ] && [ -f "$EXECUTABLE" ]; then
    echo "Копирую исполняемый файл..."
    cp "$EXECUTABLE" "$DERIVED_APP/Calorigram"
    echo "✅ Скопировано в: $DERIVED_APP/Calorigram"
    ls -lh "$DERIVED_APP/Calorigram"
else
    echo "❌ Не удалось найти файлы"
    echo "DerivedData: $DERIVED_APP"
    echo "Executable: $EXECUTABLE"
fi
