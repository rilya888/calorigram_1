//
//  CalorigramUITests.swift
//  CalorigramUITests
//
//  UI тесты для приложения Calorigram
//

import XCTest

final class CalorigramUITests: XCTestCase {

    override func setUpWithError() throws {
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchArguments = ["UI_TESTING"]
        app.launch()
    }

    override func tearDownWithError() throws {
        // Clean up after tests
    }

    func testAppLaunch() throws {
        let app = XCUIApplication()

        // Проверяем, что приложение запустилось
        XCTAssertTrue(app.state == .runningForeground)

        // Проверяем наличие основного окна
        let window = app.windows.firstMatch
        XCTAssertTrue(window.exists)
    }

    func testTabBarNavigation() throws {
        let app = XCUIApplication()

        // Ждем загрузки приложения
        let tabBar = app.tabBars.firstMatch
        XCTAssertTrue(tabBar.waitForExistence(timeout: 10))

        // Проверяем наличие всех вкладок
        let homeTab = tabBar.buttons["Главная"]
        let diaryTab = tabBar.buttons["Дневник"]
        let analysisTab = tabBar.buttons["Анализ"]
        let statsTab = tabBar.buttons["Статистика"]
        let profileTab = tabBar.buttons["Профиль"]

        XCTAssertTrue(homeTab.exists)
        XCTAssertTrue(diaryTab.exists)
        XCTAssertTrue(analysisTab.exists)
        XCTAssertTrue(statsTab.exists)
        XCTAssertTrue(profileTab.exists)
    }

    func testHomeScreenElements() throws {
        let app = XCUIApplication()

        // Переходим на вкладку Главная
        let tabBar = app.tabBars.firstMatch
        tabBar.buttons["Главная"].tap()

        // Проверяем основные элементы главного экрана
        let caloriesLabel = app.staticTexts.containing(NSPredicate(format: "label CONTAINS 'калорий'")).firstMatch
        XCTAssertTrue(caloriesLabel.waitForExistence(timeout: 5))

        // Проверяем наличие кругового прогресса (может быть представлен как изображение или кастомная view)
        // Note: Точное определение зависит от реализации UI
    }

    func testDiaryScreenNavigation() throws {
        let app = XCUIApplication()

        // Переходим на вкладку Дневник
        let tabBar = app.tabBars.firstMatch
        tabBar.buttons["Дневник"].tap()

        // Проверяем, что экран дневника загрузился
        let diaryTitle = app.staticTexts["Дневник питания"]
        XCTAssertTrue(diaryTitle.waitForExistence(timeout: 5))
    }

    func testAddMealFlow() throws {
        let app = XCUIApplication()

        // Переходим на вкладку Дневник
        app.tabBars.firstMatch.buttons["Дневник"].tap()

        // Ищем кнопку добавления приема пищи
        let addButton = app.buttons["plus"]
        if addButton.waitForExistence(timeout: 5) {
            addButton.tap()

            // Проверяем открытие модального окна добавления
            let modalTitle = app.staticTexts["Добавить прием пищи"]
            XCTAssertTrue(modalTitle.waitForExistence(timeout: 5))
        }
    }

    func testAnalysisScreen() throws {
        let app = XCUIApplication()

        // Переходим на вкладку Анализ
        app.tabBars.firstMatch.buttons["Анализ"].tap()

        // Проверяем элементы экрана анализа
        let textField = app.textFields.firstMatch
        XCTAssertTrue(textField.waitForExistence(timeout: 5))

        // Проверяем наличие кнопки анализа
        let analyzeButton = app.buttons["Анализировать"]
        XCTAssertTrue(analyzeButton.waitForExistence(timeout: 5))
    }

    func testStatsScreen() throws {
        let app = XCUIApplication()

        // Переходим на вкладку Статистика
        app.tabBars.firstMatch.buttons["Статистика"].tap()

        // Проверяем наличие элементов статистики
        let statsTitle = app.staticTexts["Статистика"]
        XCTAssertTrue(statsTitle.waitForExistence(timeout: 5))
    }

    func testProfileScreen() throws {
        let app = XCUIApplication()

        // Переходим на вкладку Профиль
        app.tabBars.firstMatch.buttons["Профиль"].tap()

        // Проверяем элементы профиля
        let profileTitle = app.staticTexts["Профиль"]
        XCTAssertTrue(profileTitle.waitForExistence(timeout: 5))
    }

    func testAuthenticationFlow() throws {
        let app = XCUIApplication()

        // Если пользователь не авторизован, должен показаться экран входа
        let loginButton = app.buttons["Войти"]
        let registerButton = app.buttons["Зарегистрироваться"]

        if loginButton.waitForExistence(timeout: 5) {
            // Проверяем наличие полей для входа
            let emailField = app.textFields["Email"]
            let passwordField = app.secureTextFields["Пароль"]

            XCTAssertTrue(emailField.exists)
            XCTAssertTrue(passwordField.exists)
        } else if registerButton.waitForExistence(timeout: 5) {
            // Проверяем наличие полей для регистрации
            let emailField = app.textFields["Email"]
            let passwordField = app.secureTextFields["Пароль"]
            let nameField = app.textFields["Имя"]

            XCTAssertTrue(emailField.exists)
            XCTAssertTrue(passwordField.exists)
            XCTAssertTrue(nameField.exists)
        }
    }

    func testModalDismissal() throws {
        let app = XCUIApplication()

        // Переходим на вкладку Дневник
        app.tabBars.firstMatch.buttons["Дневник"].tap()

        // Открываем модальное окно добавления приема пищи
        let addButton = app.buttons["plus"]
        if addButton.waitForExistence(timeout: 5) {
            addButton.tap()

            // Ждем открытия модального окна
            let modalTitle = app.staticTexts["Добавить прием пищи"]
            XCTAssertTrue(modalTitle.waitForExistence(timeout: 5))

            // Ищем кнопку закрытия (может быть крестик или "Отмена")
            let closeButton = app.buttons["xmark"].firstMatch
            if closeButton.exists {
                closeButton.tap()
                // Проверяем, что модальное окно закрылось
                XCTAssertFalse(modalTitle.exists)
            }
        }
    }

    // MARK: - Performance Tests

    func testAppLaunchPerformance() throws {
        let app = XCUIApplication()
        measure(metrics: [XCTApplicationLaunchMetric()]) {
            app.launch()
        }
    }

    func testTabSwitchingPerformance() throws {
        let app = XCUIApplication()
        let tabBar = app.tabBars.firstMatch

        measure {
            tabBar.buttons["Главная"].tap()
            tabBar.buttons["Дневник"].tap()
            tabBar.buttons["Анализ"].tap()
            tabBar.buttons["Статистика"].tap()
            tabBar.buttons["Профиль"].tap()
        }
    }
}
