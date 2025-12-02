//
//  AuthViewModelTests.swift
//  CalorigramTests
//
//  Unit тесты для AuthViewModel
//

import XCTest
@testable import Calorigram

@MainActor
final class AuthViewModelTests: XCTestCase {
    var viewModel: AuthViewModel!
    var mockAPIService: MockAPIService!

    override func setUp() {
        super.setUp()
        mockAPIService = MockAPIService()
        viewModel = AuthViewModel()
        // Note: Для полноценного тестирования нужно внедрение зависимости
    }

    override func tearDown() {
        viewModel = nil
        mockAPIService = nil
        super.tearDown()
    }

    func testInitialState() {
        XCTAssertFalse(viewModel.isAuthenticated)
        XCTAssertNil(viewModel.currentUser)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
    }

    func testCheckAuthStatus_NoToken() async {
        // Given
        let mockKeychain = MockKeychainService()
        mockKeychain.shouldReturnNil = true

        // When
        viewModel.checkAuthStatus()

        // Then
        XCTAssertFalse(viewModel.isAuthenticated)
        XCTAssertNil(viewModel.currentUser)
        XCTAssertFalse(viewModel.isLoading)
    }

    func testCheckAuthStatus_WithToken_Success() async {
        // Given
        let mockUser = MockAPIService.createMockUser()
        mockAPIService.setMockUser(mockUser)

        // When
        viewModel.checkAuthStatus()

        // Then
        // Note: Требуется внедрение зависимости для полноценного тестирования
        XCTAssertFalse(viewModel.isLoading)
    }

    func testLogin_ValidCredentials_Success() async {
        // Given
        let email = "test@example.com"
        let password = "password123"

        // When
        viewModel.login(email: email, password: password)

        // Then
        XCTAssertTrue(viewModel.isLoading)
        // Note: Требуется внедрение зависимости для полноценного тестирования
    }

    func testRegister_ValidData_Success() async {
        // Given
        let email = "newuser@example.com"
        let password = "password123"
        let name = "Test User"

        // When
        viewModel.register(email: email, password: password, name: name)

        // Then
        XCTAssertTrue(viewModel.isLoading)
        // Note: Требуется внедрение зависимости для полноценного тестирования
    }

    func testLogout() {
        // Given
        viewModel.isAuthenticated = true
        viewModel.currentUser = MockAPIService.createMockUser()

        // When
        viewModel.logout()

        // Then
        XCTAssertFalse(viewModel.isAuthenticated)
        XCTAssertNil(viewModel.currentUser)
        XCTAssertNil(viewModel.errorMessage)
    }

    func testIsUserRegistered_ProfileIncomplete() {
        // Given
        let incompleteUser = User(
            id: 1,
            telegramId: nil,
            email: "test@example.com",
            name: "Test",
            gender: nil,  // incomplete
            age: nil,
            height: nil,
            weight: nil,
            activityLevel: nil,
            goal: nil,
            dailyCalories: nil,
            targetCalories: nil,
            targetProtein: nil,
            targetFat: nil,
            targetCarbs: nil,
            subscriptionType: "trial",
            subscriptionExpiresAt: nil,
            isPremium: false
        )

        // When & Then
        XCTAssertFalse(viewModel.isUserRegistered(incompleteUser))
    }

    func testIsUserRegistered_ProfileComplete() {
        // Given
        let completeUser = MockAPIService.createMockUser()

        // When & Then
        XCTAssertTrue(viewModel.isUserRegistered(completeUser))
    }
}

// MARK: - Mock Services for Testing
class MockKeychainService {
    var shouldReturnNil = false
    var storedValues: [String: String] = [:]

    func get(forKey key: String) -> String? {
        return shouldReturnNil ? nil : storedValues[key]
    }

    func save(_ value: String, forKey key: String) {
        storedValues[key] = value
    }

    func delete(forKey key: String) {
        storedValues.removeValue(forKey: key)
    }
}
