#!/bin/bash
# Скрипт для проверки покрытия тестами iOS проекта Calorigram

echo "🔍 Проверка покрытия тестами iOS проекта Calorigram"
echo "=================================================="

# Проверяем наличие xcodebuild
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ xcodebuild не найден. Установите Xcode Command Line Tools."
    exit 1
fi

# Проверяем наличие проекта
if [ ! -f "Calorigram.xcodeproj/project.pbxproj" ]; then
    echo "❌ Файл Calorigram.xcodeproj/project.pbxproj не найден"
    exit 1
fi

echo "📊 Подсчет количества тестовых файлов..."
echo ""

# Подсчет файлов
UNIT_TESTS=$(find CalorigramTests -name "*.swift" | wc -l)
UI_TESTS=$(find CalorigramUITests -name "*.swift" 2>/dev/null | wc -l)
TOTAL_TESTS=$((UNIT_TESTS + UI_TESTS))

echo "📁 Структура тестов:"
echo "  Unit Tests: $UNIT_TESTS файлов"
echo "  UI Tests: $UI_TESTS файлов"
echo "  Всего: $TOTAL_TESTS файлов"
echo ""

# Список тестовых файлов
echo "📋 Тестовые файлы:"
echo ""
echo "Unit Tests:"
find CalorigramTests -name "*.swift" | sed 's/^/  - /'
echo ""
echo "UI Tests:"
find CalorigramUITests -name "*.swift" 2>/dev/null | sed 's/^/  - /' || echo "  (UI тесты не найдены)"
echo ""

# Анализ покрытия кода (примерная оценка)
echo "🎯 Оценка покрытия кода:"
echo ""

# Подсчет основных компонентов
VIEWMODELS=$(find Calorigram/ViewModels -name "*.swift" | wc -l)
SERVICES=$(find Calorigram/Services -name "*.swift" | wc -l)
MODELS=$(find Calorigram/Models -name "*.swift" | wc -l)
VIEWS=$(find Calorigram/Views -name "*.swift" | wc -l)

echo "📊 Компоненты проекта:"
echo "  ViewModels: $VIEWMODELS"
echo "  Services: $SERVICES"
echo "  Models: $MODELS"
echo "  Views: $VIEWS"
echo ""

# Оценка покрытия
VIEWMODEL_TESTS=$(find CalorigramTests -name "*ViewModelTests.swift" | wc -l)
SERVICE_TESTS=$(find CalorigramTests -name "*ServiceTests.swift" | wc -l)
MODEL_TESTS=$(find CalorigramTests -name "ModelTests.swift" | wc -l)

VIEWMODEL_COVERAGE=$((VIEWMODEL_TESTS * 100 / VIEWMODELS))
SERVICE_COVERAGE=$((SERVICE_TESTS * 100 / SERVICES))
MODEL_COVERAGE=$((MODEL_TESTS * 100 / MODELS))

echo "📈 Текущее покрытие:"
echo "  ViewModels: $VIEWMODEL_COVERAGE% ($VIEWMODEL_TESTS/$VIEWMODELS)"
echo "  Services: $SERVICE_COVERAGE% ($SERVICE_TESTS/$SERVICES)"
echo "  Models: $MODEL_COVERAGE% ($MODEL_TESTS/$MODELS)"
echo ""

TOTAL_COMPONENTS=$((VIEWMODELS + SERVICES + MODELS))
TOTAL_TESTS_COMPONENTS=$((VIEWMODEL_TESTS + SERVICE_TESTS + MODEL_TESTS))
OVERALL_COVERAGE=$((TOTAL_TESTS_COMPONENTS * 100 / TOTAL_COMPONENTS))

echo "🎯 Общее покрытие компонентов: $OVERALL_COVERAGE% ($TOTAL_TESTS_COMPONENTS/$TOTAL_COMPONENTS)"
echo ""

# Запуск тестов (если возможно)
echo "🚀 Запуск тестов..."
echo ""

if [ -f "Calorigram.xcodeproj" ]; then
    echo "Запуск Unit Tests..."
    xcodebuild test \
        -project Calorigram.xcodeproj \
        -scheme Calorigram \
        -destination 'platform=iOS Simulator,name=iPhone 14,OS=latest' \
        -testPlan CalorigramTests \
        -resultBundlePath TestResults \
        -quiet 2>/dev/null

    TEST_EXIT_CODE=$?

    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo "✅ Unit тесты пройдены успешно"
    else
        echo "❌ Некоторые Unit тесты не пройдены (exit code: $TEST_EXIT_CODE)"
    fi

    # Попытка запуска UI тестов
    echo ""
    echo "Запуск UI Tests..."
    xcodebuild test \
        -project Calorigram.xcodeproj \
        -scheme Calorigram \
        -destination 'platform=iOS Simulator,name=iPhone 14,OS=latest' \
        -testPlan CalorigramUITests \
        -resultBundlePath UITestResults \
        -quiet 2>/dev/null

    UI_TEST_EXIT_CODE=$?

    if [ $UI_TEST_EXIT_CODE -eq 0 ]; then
        echo "✅ UI тесты пройдены успешно"
    else
        echo "❌ Некоторые UI тесты не пройдены (exit code: $UI_TEST_EXIT_CODE)"
    fi

else
    echo "⚠️  Xcode проект не найден. Запустите тесты вручную в Xcode."
fi

echo ""
echo "📝 Рекомендации для улучшения покрытия:"
echo ""

if [ $OVERALL_COVERAGE -lt 70 ]; then
    echo "🎯 Для достижения 70% покрытия:"
    echo "  1. Добавить тесты для оставшихся ViewModels"
    echo "  2. Протестировать все Services"
    echo "  3. Добавить интеграционные тесты"
    echo "  4. Улучшить UI тесты"
fi

if [ $OVERALL_COVERAGE -ge 70 ]; then
    echo "🎉 Отличное покрытие тестами!"
    echo "  Продолжайте добавлять тесты для новых функций."
fi

echo ""
echo "📊 Итоговая оценка:"

if [ $OVERALL_COVERAGE -ge 80 ]; then
    echo "⭐⭐⭐⭐⭐ Отличное покрытие (80%+)"
elif [ $OVERALL_COVERAGE -ge 70 ]; then
    echo "⭐⭐⭐⭐ Хорошее покрытие (70-79%)"
elif [ $OVERALL_COVERAGE -ge 60 ]; then
    echo "⭐⭐⭐ Удовлетворительное покрытие (60-69%)"
elif [ $OVERALL_COVERAGE -ge 50 ]; then
    echo "⭐⭐ Низкое покрытие (50-59%)"
else
    echo "⭐ Критически низкое покрытие (<50%)"
fi

echo ""
echo "Для детального отчета о покрытии используйте Xcode Coverage Reports"
