# Что изменилось в iOS приложении

## Новый flow регистрации (как в Telegram боте)

### Было:
```
[Auth] → [Onboarding сразу] → [Main]
```

### Стало:
```
[Auth] → [Welcome приветствие] → [Onboarding] → [Main]
       ↓
   Email/Phone/Apple выбор
```

## Изменения в коде

### 1. Новые файлы

#### `WelcomeScreen.swift`
- Приветственный экран после регистрации
- Показывает имя пользователя
- Описывает возможности приложения
- Кнопка "Начать" → переход к Onboarding

#### `RegistrationMethodView.swift` (в AuthView.swift)
- Выбор способа регистрации: Email, Телефон, Apple ID
- Красивые карточки с иконками и описаниями
- Анимированные переходы

### 2. Обновленные файлы

#### `ContentView.swift`
**Добавлено:**
- Флаг `hasSeenWelcome` (AppStorage) → отслеживает, видел ли пользователь Welcome
- `isUserRegistered` → проверяет, заполнен ли профиль (age, height, weight)
- `resetOnboardingFlagsIfNeeded()` → автоматически сбрасывает флаги для существующих пользователей

**Логика:**
```swift
if !hasSeenWelcome && !isUserRegistered {
    // Новый пользователь → WelcomeScreen
} else if !hasCompletedOnboarding && !isUserRegistered {
    // После Welcome → OnboardingView
} else {
    // Профиль заполнен → MainTabView
}
```

#### `AuthView.swift`
**Добавлено:**
- `enum RegistrationMethod` → Email, Phone, Apple
- `RegistrationMethodView` → компонент выбора способа
- `showRegistrationMethod` → управляет отображением выбора способа
- Кнопка "Назад" → возврат к выбору способа

#### `EmailAuthView.swift`
**Изменено:**
- `isLoginMode` теперь передается через `@Binding` (управляется из AuthView)
- Удален встроенный переключатель Login/Register (теперь в AuthView)

#### `AuthViewModel.swift`
**Добавлено:**
- После регистрации вызывается `loadCurrentUser()` для загрузки полных данных
- После входа вызывается `loadCurrentUser()` для загрузки полных данных
- После phone/Apple авторизации также загружаются данные

## Backend изменения

### `backend/app/main.py`
- Исправлен импорт: `app.blocks.profile` → `app.api.profile`
- Исправлена синтаксическая ошибка (неправильные отступы)

### `backend/app/api/auth.py`
- Добавлено логирование создания пользователя
- Добавлена проверка, что пользователь сохранен в базе

### `backend/app/api/profile.py`
- Добавлена поддержка поля `gender` в обновлении профиля
- Исправлены hardcoded данные для соответствия модели User в iOS
- Добавлен поиск пользователя через credentials, если не найден по ID
- Добавлено логирование всех операций

## Как это работает

### Сценарий 1: Новый пользователь
```
1. Запуск → AuthView (не авторизован)
2. Выбор Email → EmailAuthView (isLoginMode = false)
3. Регистрация → Backend создает user + credentials
4. Успех → isAuthenticated = true, currentUser загружается
5. ContentView проверяет: !hasSeenWelcome && !isUserRegistered
6. Показывается WelcomeScreen
7. "Начать" → hasSeenWelcome = true, showOnboarding = true
8. Показывается OnboardingView
9. Заполнение → Backend обновляет профиль
10. Завершение → hasCompletedOnboarding = true
11. Показывается MainTabView
```

### Сценарий 2: Повторный вход
```
1. Запуск → AuthView (токен удален после logout)
2. Вход → Backend возвращает токены + user data
3. currentUser.age/height/weight != nil → isUserRegistered = true
4. resetOnboardingFlagsIfNeeded() → hasSeenWelcome = true, hasCompletedOnboarding = true
5. Показывается MainTabView (сразу)
```

### Сценарий 3: Перезапуск приложения
```
1. Запуск → checkAuthStatus() → isAuthenticated = true (токен в Keychain)
2. loadCurrentUser() → загрузка данных с backend
3. isUserRegistered = true → resetOnboardingFlagsIfNeeded()
4. Показывается MainTabView (сразу)
```

## Что исправлено

### iOS
✅ Добавлен WelcomeScreen (как в Telegram боте)  
✅ Добавлен выбор способа регистрации (Email/Phone/Apple)  
✅ Флаги автоматически сбрасываются для существующих пользователей  
✅ При повторном входе не показывается Welcome/Onboarding

### Backend
✅ Исправлен импорт profile модуля  
✅ Добавлена поддержка gender в profile update  
✅ Добавлено логирование регистрации и проверки пользователя  
✅ Исправлена структура ответа профиля (все поля модели User)

## Следующие шаги

1. **Пересоберите проект в Xcode**
2. **Протестируйте все сценарии**
3. **Проверьте логи** (Xcode + Railway)
4. **Если ошибки** → проверьте файлы документации

Все изменения готовы к тестированию!

