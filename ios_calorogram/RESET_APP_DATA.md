# Как сбросить данные приложения БЕЗ кнопки

## Проблема
Регистрация не завершается, кнопки "Очистить данные" нет в профиле.

## Решение 1: Удалить приложение с симулятора (самое простое)

### Шаги:
1. **Остановите приложение в Xcode:** ⌘. (Command + точка)
2. **В симуляторе:**
   - Долгое нажатие на иконку Calorigram
   - Нажмите **"-"** (удалить)
   - Подтвердите удаление
3. **Запустите из Xcode:** ⌘R

**Результат:** Все данные (Keychain, AppStorage) будут очищены.

## Решение 2: Сбросить симулятор полностью

### В Xcode:
```
Device → Erase All Content and Settings...
```

Подождите перезагрузки симулятора, затем запустите приложение (⌘R).

## Решение 3: Изменить код для сброса флагов

Добавьте в `ContentView.swift` временную кнопку:

```swift
// В начале body, перед Group
.onAppear {
    // ВРЕМЕННО: Принудительно сбрасываем флаги при каждом запуске
    UserDefaults.standard.removeObject(forKey: "hasCompletedOnboarding")
    UserDefaults.standard.removeObject(forKey: "hasSeenWelcome")
    authViewModel.checkAuthStatus()
}
```

Это будет сбрасывать флаги при каждом запуске.

## Решение 4: Через терминал (удалить данные симулятора)

```bash
# Найти UUID симулятора
xcrun simctl list devices | grep Booted

# Удалить приложение (замените SIMULATOR_UUID на реальный)
xcrun simctl uninstall SIMULATOR_UUID com.calorigram.app

# Или сбросить весь симулятор
xcrun simctl erase SIMULATOR_UUID
```

## Рекомендация

**Решение 1** - самое простое и быстрое:
1. Долгое нажатие на иконку → удалить
2. ⌘R для запуска

После этого:
- Keychain очищен (нет токена)
- AppStorage очищен (hasSeenWelcome = false)
- Должен показаться **AuthView**

Попробуйте Решение 1 прямо сейчас!

