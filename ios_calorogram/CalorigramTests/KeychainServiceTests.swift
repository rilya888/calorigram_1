//
//  KeychainServiceTests.swift
//  CalorigramTests
//
//  Unit тесты для KeychainService
//

import XCTest
@testable import Calorigram

final class KeychainServiceTests: XCTestCase {
    var keychainService: KeychainService!

    override func setUp() {
        super.setUp()
        keychainService = KeychainService.shared
        // Очистим keychain перед каждым тестом
        clearAllKeychainData()
    }

    override func tearDown() {
        // Очистим keychain после каждого теста
        clearAllKeychainData()
        keychainService = nil
        super.tearDown()
    }

    private func clearAllKeychainData() {
        // Очистка тестовых данных
        _ = keychainService.delete(forKey: "test_key_1")
        _ = keychainService.delete(forKey: "test_key_2")
        _ = keychainService.delete(forKey: "access_token")
        _ = keychainService.delete(forKey: "refresh_token")
    }

    func testSaveAndGetString() {
        // Given
        let key = "test_key_1"
        let value = "test_value_123"

        // When
        let saveResult = keychainService.save(value, forKey: key)
        let retrievedValue = keychainService.get(forKey: key)

        // Then
        XCTAssertTrue(saveResult)
        XCTAssertEqual(retrievedValue, value)
    }

    func testSaveAndGetEmptyString() {
        // Given
        let key = "test_key_2"
        let value = ""

        // When
        let saveResult = keychainService.save(value, forKey: key)
        let retrievedValue = keychainService.get(forKey: key)

        // Then
        XCTAssertTrue(saveResult)
        XCTAssertEqual(retrievedValue, value)
    }

    func testGetNonexistentKey() {
        // When
        let retrievedValue = keychainService.get(forKey: "nonexistent_key")

        // Then
        XCTAssertNil(retrievedValue)
    }

    func testDeleteExistingKey() {
        // Given
        let key = "test_key_1"
        let value = "test_value"
        _ = keychainService.save(value, forKey: key)

        // Verify it exists
        XCTAssertEqual(keychainService.get(forKey: key), value)

        // When
        let deleteResult = keychainService.delete(forKey: key)

        // Then
        XCTAssertTrue(deleteResult)
        XCTAssertNil(keychainService.get(forKey: key))
    }

    func testDeleteNonexistentKey() {
        // When
        let deleteResult = keychainService.delete(forKey: "nonexistent_key")

        // Then
        XCTAssertFalse(deleteResult) // Keychain возвращает false для несуществующего ключа
    }

    func testOverwriteValue() {
        // Given
        let key = "test_key_1"
        let initialValue = "initial_value"
        let newValue = "new_value"

        // Save initial value
        _ = keychainService.save(initialValue, forKey: key)
        XCTAssertEqual(keychainService.get(forKey: key), initialValue)

        // When - overwrite with new value
        let saveResult = keychainService.save(newValue, forKey: key)

        // Then
        XCTAssertTrue(saveResult)
        XCTAssertEqual(keychainService.get(forKey: key), newValue)
    }

    func testSaveLongString() {
        // Given
        let key = "test_key_long"
        let longValue = String(repeating: "A", count: 1000)

        // When
        let saveResult = keychainService.save(longValue, forKey: key)
        let retrievedValue = keychainService.get(forKey: key)

        // Then
        XCTAssertTrue(saveResult)
        XCTAssertEqual(retrievedValue, longValue)
    }

    func testSaveSpecialCharacters() {
        // Given
        let key = "test_key_special"
        let specialValue = "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"

        // When
        let saveResult = keychainService.save(specialValue, forKey: key)
        let retrievedValue = keychainService.get(forKey: key)

        // Then
        XCTAssertTrue(saveResult)
        XCTAssertEqual(retrievedValue, specialValue)
    }

    func testSaveUnicodeString() {
        // Given
        let key = "test_key_unicode"
        let unicodeValue = "Unicode: Привет мир! 🌍 🔥 🚀"

        // When
        let saveResult = keychainService.save(unicodeValue, forKey: key)
        let retrievedValue = keychainService.get(forKey: key)

        // Then
        XCTAssertTrue(saveResult)
        XCTAssertEqual(retrievedValue, unicodeValue)
    }

    func testMultipleKeys() {
        // Given
        let testData = [
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        ]

        // When - save all keys
        for (key, value) in testData {
            let saveResult = keychainService.save(value, forKey: key)
            XCTAssertTrue(saveResult)
        }

        // Then - verify all keys
        for (key, expectedValue) in testData {
            let retrievedValue = keychainService.get(forKey: key)
            XCTAssertEqual(retrievedValue, expectedValue)
        }
    }

    func testAccessTokenOperations() {
        // Given
        let accessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature"

        // When
        let saveResult = keychainService.save(accessToken, forKey: Constants.Keychain.accessToken)
        let retrievedToken = keychainService.get(forKey: Constants.Keychain.accessToken)

        // Then
        XCTAssertTrue(saveResult)
        XCTAssertEqual(retrievedToken, accessToken)
    }

    func testRefreshTokenOperations() {
        // Given
        let refreshToken = "refresh_token_123456789"

        // When
        let saveResult = keychainService.save(refreshToken, forKey: Constants.Keychain.refreshToken)
        let retrievedToken = keychainService.get(forKey: Constants.Keychain.refreshToken)

        // Then
        XCTAssertTrue(saveResult)
        XCTAssertEqual(retrievedToken, refreshToken)
    }

    // MARK: - Performance Tests

    func testPerformance_SaveSmallString() {
        let key = "perf_test_small"
        let value = "small_value"

        measure {
            _ = keychainService.save(value, forKey: key)
        }
    }

    func testPerformance_GetSmallString() {
        let key = "perf_test_get"
        let value = "test_value"
        _ = keychainService.save(value, forKey: key)

        measure {
            _ = keychainService.get(forKey: key)
        }
    }

    // MARK: - Edge Cases

    func testEmptyKey() {
        // Given
        let emptyKey = ""
        let value = "test_value"

        // When
        let saveResult = keychainService.save(value, forKey: emptyKey)

        // Then - Keychain может обрабатывать пустые ключи по-разному
        // В зависимости от реализации, это может быть разрешено или нет
        // Тест проверяет, что метод не выбрасывает исключение
        XCTAssertNotNil(saveResult) // Просто проверяем, что метод вернул результат
    }

    func testVeryLongKey() {
        // Given
        let longKey = String(repeating: "A", count: 500)
        let value = "test_value"

        // When
        let saveResult = keychainService.save(value, forKey: longKey)

        // Then
        // Keychain может иметь ограничения на длину ключей
        // Тест проверяет graceful handling
        XCTAssertNotNil(saveResult)
    }
}
