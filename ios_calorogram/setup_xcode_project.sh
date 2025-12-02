#!/bin/bash

# Скрипт для настройки Xcode проекта Calorigram
# Этот скрипт подготовит все необходимое для создания проекта в Xcode

set -e

echo "🚀 Настройка Xcode проекта Calorigram"
echo "======================================"
echo ""

# Проверяем наличие Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode не найден. Установите Xcode из App Store."
    exit 1
fi

echo "✅ Xcode найден"
echo ""

# Путь к директории проекта
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IOS_DIR="$PROJECT_DIR"

echo "📁 Рабочая директория: $IOS_DIR"
echo ""

# Проверяем наличие Swift файлов
if [ ! -d "$IOS_DIR/Calorigram" ]; then
    echo "❌ Директория Calorigram не найдена"
    exit 1
fi

echo "✅ Swift файлы найдены"
echo ""

# Создаем Info.plist шаблон
echo "📝 Создание Info.plist..."
cat > "$IOS_DIR/Info.plist.template" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>$(DEVELOPMENT_LANGUAGE)</string>
    <key>CFBundleDisplayName</key>
    <string>Calorigram</string>
    <key>CFBundleExecutable</key>
    <string>$(EXECUTABLE_NAME)</string>
    <key>CFBundleIdentifier</key>
    <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>$(PRODUCT_NAME)</string>
    <key>CFBundlePackageType</key>
    <string>$(PRODUCT_BUNDLE_PACKAGE_TYPE)</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSRequiresIPhoneOS</key>
    <true/>
    <key>UIApplicationSceneManifest</key>
    <dict>
        <key>UIApplicationSupportsMultipleScenes</key>
        <true/>
    </dict>
    <key>UIApplicationSupportsIndirectInputEvents</key>
    <true/>
    <key>UILaunchScreen</key>
    <dict/>
    <key>UIRequiredDeviceCapabilities</key>
    <array>
        <string>armv7</string>
    </array>
    <key>UISupportedInterfaceOrientations</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
    <key>UISupportedInterfaceOrientations~ipad</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationPortraitUpsideDown</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
    <key>NSPhotoLibraryUsageDescription</key>
    <string>Приложению нужен доступ к фото для анализа блюд</string>
    <key>NSCameraUsageDescription</key>
    <string>Приложению нужен доступ к камере для фотографирования блюд</string>
    <key>NSPhotoLibraryAddUsageDescription</key>
    <string>Приложению нужен доступ для сохранения фотографий</string>
</dict>
</plist>
EOF

echo "✅ Info.plist.template создан"
echo ""

# Создаем инструкцию
echo "📝 Создание инструкции..."
cat > "$IOS_DIR/XCODE_SETUP_INSTRUCTIONS.md" << 'EOF'
# Инструкция по созданию Xcode проекта

## Шаг 1: Создать новый проект в Xcode

1. Откройте **Xcode**
2. Выберите **File → New → Project** (⌘⇧N)
3. Выберите **iOS → App**
4. Нажмите **Next**

## Шаг 2: Настроить проект

Заполните форму:
- **Product Name:** `Calorigram`
- **Team:** Выберите вашу команду (или None)
- **Organization Identifier:** `com.calorigram` (или ваш)
- **Bundle Identifier:** `com.calorigram.app` (будет создан автоматически)
- **Interface:** **SwiftUI** ⚠️ ВАЖНО!
- **Language:** **Swift**
- **Storage:** None (или Core Data, если нужно)
- **Include Tests:** ✅ (рекомендуется)

Нажмите **Next**

## Шаг 3: Выбрать место сохранения

1. Выберите директорию: `ios_calorogram/`
2. **НЕ** создавайте новую папку для проекта
3. Нажмите **Create**

## Шаг 4: Удалить стандартные файлы

После создания проекта удалите:
- `ContentView.swift` (если он создан автоматически)
- `CalorigramApp.swift` (если он создан автоматически)

## Шаг 5: Добавить файлы проекта

1. В Xcode навигаторе найдите папку `Calorigram` (слева)
2. **Правой кнопкой** на папку `Calorigram` → **Add Files to "Calorigram"...**
3. Перейдите в `ios_calorogram/Calorigram/`
4. Выберите **все папки и файлы** внутри:
   - App/
   - Models/
   - Services/
   - ViewModels/
   - Views/
   - Utils/
5. Убедитесь, что выбрано:
   - ✅ **Copy items if needed**
   - ✅ **Create groups** (НЕ folder references!)
   - ✅ **Add to targets: Calorigram**
6. Нажмите **Add**

## Шаг 6: Настроить Sign in with Apple

1. Выберите проект в навигаторе (самый верхний элемент)
2. Выберите target **Calorigram**
3. Перейдите на вкладку **Signing & Capabilities**
4. Нажмите **"+ Capability"**
5. Найдите и добавьте **"Sign in with Apple"**

## Шаг 7: Настроить Info.plist

1. Откройте `Info.plist` в проекте
2. Добавьте следующие ключи (если их нет):
   - `NSPhotoLibraryUsageDescription`: "Приложению нужен доступ к фото для анализа блюд"
   - `NSCameraUsageDescription`: "Приложению нужен доступ к камере для фотографирования блюд"
   - `NSPhotoLibraryAddUsageDescription`: "Приложению нужен доступ для сохранения фотографий"

Или используйте созданный `Info.plist.template` как референс.

## Шаг 8: Настроить Deployment Target

1. Выберите проект в навигаторе
2. Выберите target **Calorigram**
3. Перейдите на вкладку **General**
4. Установите **iOS Deployment Target:** `16.0` или выше

## Шаг 9: Проверить настройки

1. Убедитесь, что все файлы добавлены в target:
   - Выберите любой Swift файл
   - В правой панели (File Inspector) проверьте, что **Target Membership** → **Calorigram** отмечен
2. Проверьте, что нет ошибок компиляции:
   - Нажмите **⌘B** для сборки
   - Исправьте все ошибки, если они есть

## Шаг 10: Запустить проект

1. Выберите симулятор (например, **iPhone 15 Pro**)
2. Нажмите **Run** (⌘R) или кнопку ▶️
3. Приложение должно запуститься!

## Возможные проблемы

### Ошибка: "Cannot find type"
- Убедитесь, что все файлы добавлены в target
- Проверьте, что нет циклических зависимостей

### Ошибка: "No such module"
- Убедитесь, что все файлы находятся в правильных папках
- Проверьте импорты

### Sign in with Apple не работает
- Убедитесь, что capability добавлена
- Проверьте Bundle Identifier
- На реальном устройстве должно работать

## Готово! 🎉

После успешного запуска приложение готово к использованию.
EOF

echo "✅ Инструкция создана: XCODE_SETUP_INSTRUCTIONS.md"
echo ""

echo "📋 Следующие шаги:"
echo "1. Откройте Xcode"
echo "2. Создайте новый iOS App проект (см. XCODE_SETUP_INSTRUCTIONS.md)"
echo "3. Добавьте все файлы из папки Calorigram/"
echo "4. Настройте Sign in with Apple capability"
echo "5. Запустите проект!"
echo ""
echo "✅ Подготовка завершена!"

