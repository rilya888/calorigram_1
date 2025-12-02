# Calorigram iOS App

Нативное iOS приложение для Calorigram на SwiftUI.

## Структура проекта

```
Calorigram/
├── Calorigram/
│   ├── App/
│   │   ├── CalorigramApp.swift          # Главный файл приложения
│   │   └── ContentView.swift            # Корневой view
│   ├── Models/
│   │   ├── User.swift                   # Модель пользователя
│   │   ├── Meal.swift                   # Модель приема пищи
│   │   ├── Statistics.swift             # Модель статистики
│   │   └── Subscription.swift           # Модель подписки
│   ├── Services/
│   │   ├── APIService.swift             # Базовый API сервис
│   │   ├── AuthService.swift            # Сервис авторизации
│   │   ├── KeychainService.swift        # Хранение токенов
│   │   └── AppleAuthService.swift       # Apple Sign In
│   ├── ViewModels/
│   │   ├── AuthViewModel.swift          # ViewModel для авторизации
│   │   ├── HomeViewModel.swift          # ViewModel для главного экрана
│   │   ├── DiaryViewModel.swift         # ViewModel для дневника
│   │   └── StatsViewModel.swift         # ViewModel для статистики
│   ├── Views/
│   │   ├── Auth/
│   │   │   ├── LoginView.swift          # Экран входа
│   │   │   ├── RegisterView.swift       # Экран регистрации
│   │   │   ├── PhoneAuthView.swift      # Авторизация по телефону
│   │   │   └── PhoneCodeView.swift      # Ввод SMS кода
│   │   ├── Home/
│   │   │   └── HomeView.swift           # Главный экран
│   │   ├── Diary/
│   │   │   └── DiaryView.swift          # Дневник
│   │   ├── Stats/
│   │   │   └── StatsView.swift          # Статистика
│   │   ├── Analysis/
│   │   │   └── AnalysisView.swift       # Анализ блюд
│   │   └── Profile/
│   │       └── ProfileView.swift        # Профиль
│   └── Utils/
│       ├── Extensions.swift             # Расширения
│       └── Constants.swift              # Константы
└── CalorigramTests/                     # Unit тесты
```

## Зависимости

Используется Swift Package Manager:

- **Alamofire** - HTTP networking
- **KeychainAccess** - безопасное хранение токенов

## Настройка

1. Откройте проект в Xcode
2. Установите зависимости через Swift Package Manager
3. Настройте `Constants.swift` с URL backend
4. Настройте Sign in with Apple capability в Xcode

## Backend URL

По умолчанию используется: `https://calorigramback-production.up.railway.app`

Измените в `Utils/Constants.swift` если нужно.
