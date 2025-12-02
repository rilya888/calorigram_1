# Пошаговая инструкция создания Xcode проекта

## Шаг 1: Создание проекта в Xcode

1. **Откройте Xcode**

2. **Создайте новый проект:**
   - File → New → Project (или ⌘⇧N)
   - Выберите **iOS** → **App**
   - Нажмите **Next**

3. **Настройте проект:**
   - **Product Name:** `Calorigram`
   - **Team:** Выберите свою команду (или None)
   - **Organization Identifier:** `com.yourname` (например, `com.calorigram`)
   - **Bundle Identifier:** Будет создан автоматически
   - **Interface:** **SwiftUI**
   - **Language:** **Swift**
   - **Use Core Data:** ❌ (не отмечайте)
   - **Include Tests:** ✅ (можно отметить)

4. **Сохраните проект:**
   - Выберите папку: `/Users/mac/bot_deploy_1/calorigram-monorepo/ios/`
   - Нажмите **Create**

## Шаг 2: Копирование файлов

После создания проекта, скопируйте все файлы из `ios/Calorigram/` в созданный проект:

### В Xcode:

1. **Удалите автоматически созданные файлы:**
   - Удалите `ContentView.swift` (если он создан автоматически)
   - Оставьте только `CalorigramApp.swift` (или замените его)

2. **Добавьте папки с файлами:**
   - Правой кнопкой на проект → **Add Files to "Calorigram"...**
   - Выберите папку `Calorigram/` из `ios/`
   - Убедитесь, что выбрано:
     - ✅ **Copy items if needed**
     - ✅ **Create groups** (не folder references)
   - Нажмите **Add**

3. **Проверьте структуру:**
   ```
   Calorigram/
   ├── App/
   │   ├── CalorigramApp.swift
   │   └── ContentView.swift
   ├── Models/
   │   ├── User.swift
   │   ├── Meal.swift
   │   ├── Statistics.swift
   │   └── Subscription.swift
   ├── Services/
   │   ├── APIService.swift
   │   ├── AuthService.swift
   │   ├── KeychainService.swift
   │   └── AppleAuthService.swift
   ├── ViewModels/
   │   ├── AuthViewModel.swift
   │   ├── HomeViewModel.swift
   │   ├── DiaryViewModel.swift
   │   ├── StatsViewModel.swift
   │   ├── AddMealViewModel.swift
   │   └── AnalysisViewModel.swift
   ├── Views/
   │   ├── Auth/
   │   ├── Home/
   │   ├── Diary/
   │   ├── Stats/
   │   ├── Analysis/
   │   ├── Profile/
   │   ├── Modals/
   │   └── MainTabView.swift
   └── Utils/
       ├── Constants.swift
       └── Extensions.swift
   ```

## Шаг 3: Настройка Sign in with Apple

1. **Выберите проект** в навигаторе (самый верхний элемент)

2. **Выберите target "Calorigram"**

3. **Перейдите на вкладку "Signing & Capabilities"**

4. **Нажмите "+ Capability"**

5. **Добавьте "Sign in with Apple"**

## Шаг 4: Настройка Info.plist (опционально)

Если нужно разрешить HTTP запросы (для тестирования):

1. Откройте `Info.plist`
2. Добавьте ключ `App Transport Security Settings`
3. Добавьте `Allow Arbitrary Loads` = `NO` (по умолчанию)

## Шаг 5: Запуск

1. **Выберите симулятор:**
   - Вверху Xcode выберите симулятор (например, iPhone 15 Pro)

2. **Запустите проект:**
   - Нажмите **Run** (⌘R) или кнопку ▶️

3. **Проверьте:**
   - Приложение должно запуститься
   - Должен появиться экран авторизации

## Шаг 6: Тестирование

### Тест 1: Email/Password регистрация
1. Выберите "Email" в сегментированном контроле
2. Нажмите "Регистрация"
3. Введите:
   - Email: `test@example.com`
   - Пароль: `test123456`
   - Имя: `Test User`
4. Нажмите "Зарегистрироваться"
5. Должен произойти вход и показаться главный экран

### Тест 2: Phone SMS
1. Выберите "Телефон"
2. Введите номер: `+1234567890`
3. Нажмите "Отправить код"
4. Проверьте логи backend для получения кода
5. Введите код и подтвердите

### Тест 3: Главный экран
- После входа должен показаться главный экран с круговым прогресс-баром
- Должны отображаться макросы (белки, жиры, углеводы)

## Возможные проблемы

### Ошибка компиляции: "Cannot find type 'X' in scope"
- Убедитесь, что все файлы добавлены в target "Calorigram"
- Проверьте, что нет циклических зависимостей

### Ошибка: "Sign in with Apple not configured"
- Убедитесь, что добавлена capability "Sign in with Apple"
- Проверьте Bundle Identifier в настройках проекта

### Ошибка сети: "Failed to connect"
- Проверьте, что backend запущен
- Проверьте URL в `Constants.swift`
- Убедитесь, что используется правильный backend URL

## Готово!

После успешного запуска приложение готово к использованию. Все основные функции реализованы:
- ✅ Авторизация (Email, Phone, Apple)
- ✅ Главный экран с калориями
- ✅ Дневник приемов пищи
- ✅ Статистика
- ✅ Анализ блюд
- ✅ Профиль
