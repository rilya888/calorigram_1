# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ - Файлы не копируются в .app

## Проблема

Исполняемый файл создается при линковке, но не копируется в .app bundle. Это проблема с настройками проекта.

## ✅ Решение: Добавить файлы вручную в Xcode

xcodegen не может правильно настроить проект. Нужно добавить файлы вручную.

### Шаг 1: Откройте проект

```bash
open /Users/mac/ios_calorogram/Calorigram.xcodeproj
```

### Шаг 2: Добавьте все файлы

1. В навигаторе найдите папку **Calorigram** (желтая)
2. **Правой кнопкой** → **"Add Files to 'Calorigram'..."**
3. Выберите папку `/Users/mac/ios_calorogram/Calorigram`
4. Выберите **ВСЕ** подпапки:
   - App
   - Models  
   - Services
   - ViewModels
   - Views
   - Utils
5. Убедитесь:
   - ✅ **"Create groups"** (НЕ folder references!)
   - ✅ **"Add to targets: Calorigram"**
   - ❌ НЕ отмечайте "Copy items if needed"
6. Нажмите **"Add"**

### Шаг 3: Проверьте Build Phases

1. Проект → Target "Calorigram" → **"Build Phases"**
2. **"Compile Sources"** → должно быть 34 файла
3. Если файлов нет - добавьте их вручную (кнопка "+")

### Шаг 4: Пересоберите

1. **Product → Clean Build Folder** (⌘⇧K)
2. **Product → Build** (⌘B)
3. Проверьте, что "Build Succeeded"

### Шаг 5: Запустите

1. Выберите **симулятор** (iPhone 17 Pro)
2. Нажмите **⌘R**

---

## Альтернатива: Создать проект заново в Xcode

Если ничего не помогает:

1. **File → New → Project**
2. **iOS → App**
3. Настройки:
   - Product Name: Calorigram
   - Interface: SwiftUI
   - Language: Swift
4. Сохраните в `/Users/mac/ios_calorogram/`
5. Удалите автоматически созданные файлы
6. Добавьте все файлы из папки `Calorigram/`

---

## ✅ После исправления

Проект должен:
- Компилировать все файлы
- Создавать исполняемый файл
- Копировать его в .app bundle
- Запускаться на симуляторе

