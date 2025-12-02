# Решение ошибки "is not a valid path to an executable file"

## Проблема

Xcode не может найти исполняемый файл при запуске приложения.

## ✅ Решение

### Вариант 1: В Xcode (РЕКОМЕНДУЕТСЯ)

1. **Выберите СИМУЛЯТОР** вверху Xcode:
   - Кликните на устройство (рядом с кнопкой ▶️)
   - Выберите **"iPhone 17 Pro"** или любой симулятор
   - ⚠️ НЕ выбирайте "Any iOS Device"!

2. **Очистите проект:**
   - **Product → Clean Build Folder** (⌘⇧K)

3. **Пересоберите:**
   - **Product → Build** (⌘B)
   - Дождитесь "Build Succeeded"

4. **Запустите:**
   - **Product → Run** (⌘R)

### Вариант 2: Через терминал

Выполните скрипт:

```bash
cd /Users/mac/ios_calorogram
./run_on_simulator.sh
```

Или вручную:

```bash
cd /Users/mac/ios_calorogram

# Очистить
xcodebuild -project Calorigram.xcodeproj -scheme Calorigram clean

# Собрать
xcodebuild -project Calorigram.xcodeproj \
  -scheme Calorigram \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  build

# Запустить симулятор и приложение
open -a Simulator
xcrun simctl boot "iPhone 17 Pro" 2>/dev/null
APP_PATH=$(find ~/Library/Developer/Xcode/DerivedData/Calorigram-*/Build/Products/Debug-iphonesimulator -name "Calorigram.app" | head -1)
xcrun simctl install booted "$APP_PATH"
xcrun simctl launch booted com.calorigram.Calorigram
```

---

## 🔍 Главное правило

**ВСЕГДА выбирайте СИМУЛЯТОР, а не "Any iOS Device"!**

Вверху Xcode должно быть:
```
[▶️] Calorigram > iPhone 17 Pro  ← СИМУЛЯТОР!
```

А НЕ:
```
[▶️] Calorigram > Any iOS Device  ← НЕ РАБОТАЕТ!
```

---

## ✅ После исправления

Приложение должно:
1. Собраться без ошибок
2. Установиться на симулятор
3. Запуститься
4. Показать экран авторизации

---

## 📝 Если все еще не работает

1. Закройте Xcode
2. Удалите DerivedData:
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData/Calorigram-*
   ```
3. Откройте проект заново
4. Product → Clean Build Folder (⌘⇧K)
5. Выберите симулятор
6. Product → Build (⌘B)
7. Product → Run (⌘R)

