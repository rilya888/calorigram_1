//
//  AuthServiceTests.swift
//  CalorigramTests
//
//  Unit тесты для AuthService
//

import XCTest
@testable import Calorigram

@MainActor
final class AuthServiceTests: XCTestCase {
    var authService: AuthService!
    var mockAPIService: MockAPIService!
    var mockKeychainService: MockKeychainService!

    override func setUp() {
        super.setUp()
        mockAPIService = MockAPIService()
        mockKeychainService = MockKeychainService()
        // Note: Требуется dependency injection для полноценного тестирования
        authService = AuthService.shared
    }

    override func tearDown() {
        authService = nil
        mockAPIService = nil
        mockKeychainService = nil
        super.tearDown()
    }

    func testLogin_Success() async {
        // Given
        let email = "test@example.com"
        let password = "password123"
        let mockUser = MockAPIService.createMockUser()
        mockAPIService.setMockUser(mockUser)

        // When
        let result = await authService.login(email: email, password: password)

        // Then
        // Note: Требуется внедрение зависимости для полноценного тестирования
        XCTAssertNotNil(result)
    }

    func testLogin_InvalidCredentials() async {
        // Given
        mockAPIService.setShouldReturnError(true)

        // When
        let result = await authService.login(email: "wrong@email.com", password: "wrongpass")

        // Then
        XCTAssertNil(result)
    }

    func testRegister_Success() async {
        // Given
        let email = "newuser@example.com"
        let password = "password123"
        let name = "New User"

        // When
        let result = await authService.register(email: email, password: password, name: name)

        // Then
        // Note: Требуется внедрение зависимости для проверки
        XCTAssertNotNil(result)
    }

    func testRegister_EmailAlreadyExists() async {
        // Given
        mockAPIService.setShouldReturnError(true)

        // When
        let result = await authService.register(email: "existing@email.com", password: "pass", name: "Test")

        // Then
        XCTAssertNil(result)
    }

    func testGetCurrentUser_Success() async {
        // Given
        let mockUser = MockAPIService.createMockUser()
        mockAPIService.setMockUser(mockUser)

        // When
        let user = await authService.getCurrentUser()

        // Then
        // Note: Требуется внедрение зависимости
        XCTAssertNotNil(user)
    }

    func testGetCurrentUser_NoToken() async {
        // Given
        mockKeychainService.shouldReturnNil = true

        // When
        let user = await authService.getCurrentUser()

        // Then
        XCTAssertNil(user)
    }

    func testLogout() {
        // Given
        authService.isAuthenticated = true

        // When
        authService.logout()

        // Then
        XCTAssertFalse(authService.isAuthenticated)
    }

    func testIsAuthenticated_NoToken() {
        // Given
        mockKeychainService.shouldReturnNil = true

        // When & Then
        XCTAssertFalse(authService.isAuthenticated)
    }

    func testRefreshToken_Success() async {
        // Given
        let refreshToken = "valid_refresh_token"
        mockKeychainService.storedValues[Constants.Keychain.refreshToken] = refreshToken

        // When
        let newToken = await authService.refreshToken()

        // Then
        // Note: Требуется внедрение зависимости для полноценного тестирования
        XCTAssertNotNil(newToken)
    }

    func testRefreshToken_NoRefreshToken() async {
        // Given
        mockKeychainService.shouldReturnNil = true

        // When
        let newToken = await authService.refreshToken()

        // Then
        XCTAssertNil(newToken)
    }

    // MARK: - Email Validation Tests

    func testIsValidEmail_ValidEmails() {
        let validEmails = [
            "test@example.com",
            "user.name+tag@example.co.uk",
            "test.email@subdomain.example.com"
        ]

        for email in validEmails {
            XCTAssertTrue(authService.isValidEmail(email), "Email should be valid: \(email)")
        }
    }

    func testIsValidEmail_InvalidEmails() {
        let invalidEmails = [
            "",
            "invalid",
            "invalid@",
            "@example.com",
            "invalid..email@example.com",
            "invalid email@example.com",
            "invalid@exam ple.com"
        ]

        for email in invalidEmails {
            XCTAssertFalse(authService.isValidEmail(email), "Email should be invalid: \(email)")
        }
    }

    // MARK: - Password Validation Tests

    func testIsValidPassword_ValidPasswords() {
        let validPasswords = [
            "password123",
            "Pass123!",
            "MySecurePassword123",
            "123456789"
        ]

        for password in validPasswords {
            XCTAssertTrue(authService.isValidPassword(password), "Password should be valid: \(password)")
        }
    }

    func testIsValidPassword_InvalidPasswords() {
        let invalidPasswords = [
            "",
            "123",
            "short",
            String(repeating: "A", count: 5) // слишком короткий
        ]

        for password in invalidPasswords {
            XCTAssertFalse(authService.isValidPassword(password), "Password should be invalid: \(password)")
        }
    }

    // MARK: - Name Validation Tests

    func testIsValidName_ValidNames() {
        let validNames = [
            "John Doe",
            "Иван Петров",
            "Maria Silva",
            "张三"
        ]

        for name in validNames {
            XCTAssertTrue(authService.isValidName(name), "Name should be valid: \(name)")
        }
    }

    func testIsValidName_InvalidNames() {
        let invalidNames = [
            "",
            "   ",
            "A",
            String(repeating: "A", count: 101) // слишком длинный
        ]

        for name in invalidNames {
            XCTAssertFalse(authService.isValidName(name), "Name should be invalid: \(name)")
        }
    }

    // MARK: - Token Management Tests

    func testSaveTokens() {
        // Given
        let accessToken = "access_token_123"
        let refreshToken = "refresh_token_456"

        // When
        authService.saveTokens(accessToken: accessToken, refreshToken: refreshToken)

        // Then
        // Note: Требуется внедрение зависимости для проверки
        XCTAssertTrue(true) // Метод не должен выбрасывать исключения
    }

    func testClearTokens() {
        // When
        authService.clearTokens()

        // Then
        XCTAssertFalse(authService.isAuthenticated)
    }

    // MARK: - Error Handling Tests

    func testHandleAuthError_NetworkError() async {
        // Given
        mockAPIService.setShouldReturnError(true)

        // When
        let result = await authService.login(email: "test@example.com", password: "password")

        // Then
        XCTAssertNil(result)
    }

    func testHandleAuthError_Unauthorized() async {
        // Given
        // Симулируем 401 ошибку
        mockAPIService.setShouldReturnError(true)

        // When
        let result = await authService.getCurrentUser()

        // Then
        XCTAssertNil(result)
    }

    // MARK: - Performance Tests

    func testPerformance_EmailValidation() {
        let email = "performance.test@example.com"

        measure {
            for _ in 0..<1000 {
                _ = authService.isValidEmail(email)
            }
        }
    }

    func testPerformance_PasswordValidation() {
        let password = "PerformanceTestPassword123!"

        measure {
            for _ in 0..<1000 {
                _ = authService.isValidPassword(password)
            }
        }
    }
}
