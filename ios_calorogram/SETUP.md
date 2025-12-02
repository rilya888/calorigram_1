# Настройка iOS проекта

## Создание Xcode проекта

1. Откройте Xcode
2. Создайте новый проект: File → New → Project
3. Выберите "iOS" → "App"
4. Название: `Calorigram`
5. Interface: `SwiftUI`
6. Language: `Swift`
7. Сохраните проект в папку `ios/`

## Настройка структуры

1. Скопируйте все файлы из `ios/Calorigram/` в созданный Xcode проект
2. Убедитесь, что структура папок соответствует:
   - Models/
   - Services/
   - ViewModels/
   - Views/
   - Utils/

## Настройка Sign in with Apple

1. В Xcode выберите проект в навигаторе
2. Выберите target "Calorigram"
3. Перейдите на вкладку "Signing & Capabilities"
4. Нажмите "+ Capability"
5. Добавьте "Sign in with Apple"

## Настройка Info.plist

Добавьте в Info.plist (если нужно):
```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
</dict>
```

## Зависимости (опционально)

Если хотите использовать Alamofire вместо URLSession:

1. File → Add Packages...
2. Добавьте: `https://github.com/Alamofire/Alamofire.git`
3. Версия: `5.8.0` или выше

Если хотите использовать KeychainAccess:

1. File → Add Packages...
2. Добавьте: `https://github.com/kishikawakatsumi/KeychainAccess.git`
3. Версия: `4.2.0` или выше

**Примечание:** Текущая реализация использует только стандартные библиотеки iOS (URLSession, Security framework), поэтому дополнительные зависимости не обязательны.

## Настройка Backend URL

Измените `Constants.swift` если нужно использовать другой backend URL:
```swift
static let apiBaseURL = "https://your-backend-url.com/api"
```

## Запуск

1. Выберите симулятор или устройство
2. Нажмите Run (⌘R)
3. Приложение должно запуститься

## Тестирование

1. Протестируйте регистрацию через email/password
2. Протестируйте авторизацию по телефону (в dev режиме код логируется в консоль backend)
3. Протестируйте Apple Sign In (требует реальное устройство или правильную настройку в Xcode)
