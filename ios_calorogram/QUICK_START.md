# Быстрый старт iOS приложения

## Шаги для запуска

### 1. Создать Xcode проект

```bash
# Откройте Xcode и создайте новый проект:
# File → New → Project → iOS → App
# Название: Calorigram
# Interface: SwiftUI
# Language: Swift
```

### 2. Скопировать файлы

Скопируйте все файлы из `ios/Calorigram/` в созданный Xcode проект:
- Models/
- Services/
- ViewModels/
- Views/
- Utils/
- App/

### 3. Настроить Sign in with Apple

1. В Xcode выберите проект
2. Target → Signing & Capabilities
3. Нажмите "+ Capability"
4. Добавьте "Sign in with Apple"

### 4. Запустить

1. Выберите симулятор (iPhone 14 или новее)
2. Нажмите Run (⌘R)

## Тестирование

### Email/Password
1. Выберите "Email" в сегментированном контроле
2. Нажмите "Регистрация"
3. Введите email, пароль, имя
4. Нажмите "Зарегистрироваться"

### Phone SMS
1. Выберите "Телефон"
2. Введите номер телефона (например: +1234567890)
3. Нажмите "Отправить код"
4. В development режиме код будет в логах backend
5. Введите код и подтвердите

### Apple Sign In
1. Выберите "Apple ID"
2. Нажмите кнопку "Sign in with Apple"
3. Подтвердите авторизацию

## Структура файлов

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
│   └── StatsViewModel.swift
├── Views/
│   ├── Auth/
│   │   ├── AuthView.swift
│   │   ├── EmailAuthView.swift
│   │   ├── PhoneAuthView.swift
│   │   └── AppleAuthView.swift
│   ├── Home/
│   │   └── HomeView.swift
│   ├── Diary/
│   │   └── DiaryView.swift
│   ├── Stats/
│   │   └── StatsView.swift
│   ├── Profile/
│   │   └── ProfileView.swift
│   └── MainTabView.swift
└── Utils/
    ├── Constants.swift
    └── Extensions.swift
```

## Важные замечания

1. **Backend URL** - по умолчанию используется Railway production URL. Измените в `Constants.swift` если нужно.

2. **JWT токены** - автоматически сохраняются в Keychain и обновляются при истечении.

3. **Phone SMS** - в development режиме коды логируются в консоль backend.

4. **Apple Sign In** - требует настройки capability в Xcode и работает только на реальных устройствах или правильно настроенных симуляторах.

## Следующие шаги

После успешного запуска можно:
1. Добавить модальное окно для добавления приема пищи
2. Реализовать анализ блюд по фото
3. Добавить редактирование профиля
4. Улучшить UI/UX
