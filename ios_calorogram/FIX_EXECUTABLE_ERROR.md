# Как исправить ошибку "is not a valid path to an executable file"

## Проблема

Ошибка возникает, когда Xcode не может найти исполняемый файл приложения после сборки.

## Решения

### Решение 1: Очистить и пересобрать проект

**В Xcode:**
1. **Product → Clean Build Folder** (⌘⇧K)
2. **Product → Build** (⌘B)
3. **Product → Run** (⌘R)

### Решение 2: Выбрать правильный симулятор

1. Вверху Xcode выберите **симулятор** (не "Any iOS Device")
2. Выберите конкретный симулятор, например: **iPhone 17 Pro**
3. Нажмите **⌘R** для запуска

### Решение 3: Проверить схему

1. Рядом с кнопкой запуска (▶️) нажмите на название схемы
2. Убедитесь, что выбрана схема **"Calorigram"**
3. Убедитесь, что выбран **симулятор**, а не "Any iOS Device"

### Решение 4: Пересоздать проект

Если ничего не помогает:

```bash
cd /Users/mac/ios_calorogram
rm -rf Calorigram.xcodeproj
xcodegen generate
open Calorigram.xcodeproj
```

Затем:
1. Product → Clean Build Folder (⌘⇧K)
2. Product → Build (⌘B)
3. Product → Run (⌘R)

### Решение 5: Проверить настройки схемы

1. **Product → Scheme → Edit Scheme...**
2. Вкладка **"Run"**
3. Убедитесь, что:
   - **Executable:** "Calorigram.app"
   - **Build Configuration:** Debug
4. Нажмите **Close**

---

## Быстрая проверка

Выполните в терминале:

```bash
cd /Users/mac/ios_calorogram

# Очистить build
xcodebuild -project Calorigram.xcodeproj -scheme Calorigram clean

# Собрать для симулятора
xcodebuild -project Calorigram.xcodeproj \
  -scheme Calorigram \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  build

# Проверить, создался ли .app
find ~/Library/Developer/Xcode/DerivedData/Calorigram-*/Build/Products/Debug-iphonesimulator -name "Calorigram.app"
```

Если `.app` файл найден - проект собирается правильно, проблема в настройках схемы в Xcode.

---

## Частые причины

1. **Выбран "Any iOS Device"** вместо симулятора
2. **Схема не настроена** для запуска
3. **Build не завершился** успешно
4. **DerivedData поврежден** - нужно очистить

---

## Рекомендуемый порядок действий

1. ✅ Выберите **симулятор** (не "Any iOS Device")
2. ✅ **Product → Clean Build Folder** (⌘⇧K)
3. ✅ **Product → Build** (⌘B)
4. ✅ Проверьте, что сборка успешна
5. ✅ **Product → Run** (⌘R)

Если все еще не работает - пересоздайте проект через `xcodegen generate`.

