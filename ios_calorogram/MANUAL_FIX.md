# Ручное исправление проблемы с файлами

## Проблема

xcodegen не добавляет Swift файлы в target автоматически. Нужно добавить их вручную в Xcode.

## ✅ Решение: Добавить файлы вручную в Xcode

### Шаг 1: Откройте проект в Xcode

```bash
open /Users/mac/ios_calorogram/Calorigram.xcodeproj
```

### Шаг 2: Добавьте файлы в target

1. В левой панели (навигатор) найдите папку **Calorigram** (желтая папка)

2. **Правой кнопкой** на папку **Calorigram** → **"Add Files to 'Calorigram'..."**

3. В открывшемся окне:
   - Перейдите в папку `/Users/mac/ios_calorogram/Calorigram`
   - Выберите **ВСЕ папки**: App, Models, Services, ViewModels, Views, Utils
   - Убедитесь, что отмечено:
     - ✅ **"Copy items if needed"** (НЕ отмечайте!)
     - ✅ **"Create groups"** (НЕ "Create folder references"!)
     - ✅ **"Add to targets: Calorigram"** (ОБЯЗАТЕЛЬНО!)

4. Нажмите **"Add"**

### Шаг 3: Проверьте Build Phases

1. Проект → Target "Calorigram" → вкладка **"Build Phases"**
2. Разверните **"Compile Sources"**
3. Там должны быть все `.swift` файлы (34 файла)

### Шаг 4: Пересоберите проект

1. **Product → Clean Build Folder** (⌘⇧K)
2. **Product → Build** (⌘B)
3. Дождитесь "Build Succeeded"

### Шаг 5: Запустите

1. Выберите **симулятор** (iPhone 17 Pro)
2. Нажмите **⌘R**

---

## Альтернатива: Использовать готовый проект

Если ручное добавление не работает, можно создать проект вручную в Xcode:

1. Откройте Xcode
2. **File → New → Project**
3. Выберите **iOS → App**
4. Настройки:
   - Product Name: **Calorigram**
   - Interface: **SwiftUI**
   - Language: **Swift**
   - Use Core Data: **NO**
5. Сохраните в `/Users/mac/ios_calorogram/`
6. Удалите автоматически созданные файлы
7. Добавьте все файлы из папки `Calorigram/`

---

## ✅ После исправления

Проект должен:
- Компилировать все Swift файлы
- Создавать исполняемый файл
- Запускаться на симуляторе

