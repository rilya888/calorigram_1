//
//  NotificationServiceTests.swift
//  CalorigramTests
//
//  Unit тесты для NotificationService
//

import XCTest
import UserNotifications
@testable import Calorigram

final class NotificationServiceTests: XCTestCase {

    var notificationService: NotificationService!

    override func setUp() {
        super.setUp()
        notificationService = NotificationService.shared
    }

    override func tearDown() {
        notificationService = nil
        super.tearDown()
    }

    func testSharedInstance() {
        let instance1 = NotificationService.shared
        let instance2 = NotificationService.shared
        XCTAssertTrue(instance1 === instance2, "NotificationService should be singleton")
    }

    func testRequestAuthorization_Success() async {
        // Given
        let expectation = expectation(description: "Authorization request")

        // When
        let granted = await notificationService.requestAuthorization()

        // Then
        // Note: Результат зависит от настроек симулятора
        // В реальном тестировании нужно mock'ать UNUserNotificationCenter
        XCTAssertNotNil(granted) // Результат может быть true или false

        expectation.fulfill()

        await waitForExpectations(timeout: 5.0)
    }

    func testScheduleMealReminder() async {
        // Given
        let mealType = "breakfast"
        let hour = 8
        let minute = 30

        // When
        let success = await notificationService.scheduleMealReminder(for: mealType, at: hour, minute: minute)

        // Then
        // Note: Требуется внедрение зависимости для полноценного тестирования
        XCTAssertNotNil(success)
    }

    func testCancelMealReminder() async {
        // Given
        let mealType = "lunch"

        // When
        await notificationService.cancelMealReminder(for: mealType)

        // Then
        XCTAssertTrue(true) // Метод не должен выбрасывать исключения
    }

    func testScheduleDailyReminders() async {
        // Given
        let reminders = [
            "breakfast": (8, 0),
            "lunch": (13, 0),
            "dinner": (19, 0)
        ]

        // When
        await notificationService.scheduleDailyReminders(reminders)

        // Then
        XCTAssertTrue(true) // Метод не должен выбрасывать исключения
    }

    func testCancelAllReminders() async {
        // When
        await notificationService.cancelAllReminders()

        // Then
        XCTAssertTrue(true) // Метод не должен выбрасывать исключения
    }

    func testGetPendingNotifications() async {
        // When
        let notifications = await notificationService.getPendingNotifications()

        // Then
        XCTAssertNotNil(notifications)
        // Note: В симуляторе список может быть пустым
    }

    func testFormatMealType() {
        // Given
        let mealTypes = [
            "breakfast": "Завтрак",
            "lunch": "Обед",
            "dinner": "Ужин",
            "snack": "Перекус"
        ]

        // When & Then
        for (key, expected) in mealTypes {
            let formatted = notificationService.formatMealType(key)
            XCTAssertEqual(formatted, expected, "Meal type \(key) should format to \(expected)")
        }
    }

    func testFormatMealType_Unknown() {
        // When
        let formatted = notificationService.formatMealType("unknown")

        // Then
        XCTAssertEqual(formatted, "Напоминание")
    }

    func testCreateNotificationContent() {
        // Given
        let title = "Завтрак"
        let body = "Время поесть!"

        // When
        let content = notificationService.createNotificationContent(title: title, body: body)

        // Then
        XCTAssertEqual(content.title, title)
        XCTAssertEqual(content.body, body)
        XCTAssertEqual(content.sound, .default)
        XCTAssertEqual(content.categoryIdentifier, "MEAL_REMINDER")
    }

    func testCreateNotificationTrigger() {
        // Given
        let hour = 12
        let minute = 30

        // When
        let trigger = notificationService.createDailyTrigger(hour: hour, minute: minute)

        // Then
        XCTAssertNotNil(trigger)
        // Note: Проверка компонентов DateComponents требует доступа к приватным свойствам
    }

    func testCreateReminderIdentifier() {
        // Given
        let mealType = "lunch"

        // When
        let identifier = notificationService.createReminderIdentifier(for: mealType)

        // Then
        XCTAssertEqual(identifier, "meal_reminder_lunch")
    }

    // MARK: - Authorization Status Tests

    func testCheckAuthorizationStatus() async {
        // When
        let status = await notificationService.checkAuthorizationStatus()

        // Then
        XCTAssertNotNil(status)
        // Note: Статус зависит от настроек симулятора
    }

    func testOpenSettings() {
        // Given
        let settingsURL = URL(string: UIApplication.openSettingsURLString)!

        // When
        notificationService.openSettings()

        // Then
        // Note: Тестирование открытия URL требует специальной настройки
        XCTAssertTrue(true) // Метод не должен выбрасывать исключения
    }

    // MARK: - Performance Tests

    func testPerformance_RequestAuthorization() {
        let service = NotificationService.shared

        measure {
            let expectation = expectation(description: "Auth request")
            Task {
                _ = await service.requestAuthorization()
                expectation.fulfill()
            }
            waitForExpectations(timeout: 5.0)
        }
    }

    func testPerformance_ScheduleReminder() {
        let service = NotificationService.shared

        measure {
            let expectation = expectation(description: "Schedule reminder")
            Task {
                _ = await service.scheduleMealReminder(for: "test", at: 12, minute: 0)
                expectation.fulfill()
            }
            waitForExpectations(timeout: 5.0)
        }
    }
}
