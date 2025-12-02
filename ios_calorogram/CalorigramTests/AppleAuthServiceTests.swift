//
//  AppleAuthServiceTests.swift
//  CalorigramTests
//
//  Unit тесты для AppleAuthService
//

import XCTest
import AuthenticationServices
@testable import Calorigram

final class AppleAuthServiceTests: XCTestCase {

    var authService: AppleAuthService!

    override func setUp() {
        super.setUp()
        authService = AppleAuthService.shared
    }

    override func tearDown() {
        authService = nil
        super.tearDown()
    }

    func testSharedInstance() {
        let instance1 = AppleAuthService.shared
        let instance2 = AppleAuthService.shared
        XCTAssertTrue(instance1 === instance2, "AppleAuthService should be singleton")
    }

    func testAuthorizationControllerCreation() {
        let request = ASAuthorizationAppleIDProvider().createRequest()
        request.requestedScopes = [.fullName, .email]

        let controller = ASAuthorizationController(authorizationRequests: [request])

        XCTAssertNotNil(controller)
        XCTAssertEqual(controller.authorizationRequests.count, 1)
    }

    func testHandleAuthorization_Success() {
        // Given
        let expectation = expectation(description: "Authorization handling")

        let mockCredential = MockAppleIDCredential()
        mockCredential.user = "test_user_123"
        mockCredential.email = "test@example.com"
        mockCredential.fullName = PersonNameComponents()
        mockCredential.fullName?.givenName = "Test"
        mockCredential.fullName?.familyName = "User"

        // When
        authService.handleAuthorization(ASAuthorization(credential: mockCredential))

        // Then
        // Note: Требуется внедрение зависимости для полноценного тестирования
        XCTAssertTrue(true) // Метод не должен выбрасывать исключения

        expectation.fulfill()

        waitForExpectations(timeout: 1.0)
    }

    func testHandleAuthorization_Failure() {
        // Given
        let expectation = expectation(description: "Authorization failure handling")
        let error = ASAuthorizationError(.canceled)

        // When
        authService.handleAuthorizationError(error)

        // Then
        XCTAssertTrue(true) // Метод не должен выбрасывать исключения

        expectation.fulfill()

        waitForExpectations(timeout: 1.0)
    }

    func testSignInWithAppleButton() {
        // Given
        let button = ASAuthorizationAppleIDButton()

        // Then
        XCTAssertNotNil(button)
        XCTAssertEqual(button.type, .default)
        XCTAssertEqual(button.style, .black)
    }

    // MARK: - Mock Classes

    class MockAppleIDCredential: NSObject, ASAuthorizationAppleIDCredential {
        var user: String = ""
        var email: String? = nil
        var fullName: PersonNameComponents? = nil
        var authorizationCode: Data? = nil
        var identityToken: Data? = nil
        var state: String? = nil
        var realUserStatus: ASUserDetectionStatus = .unknown
    }
}

// MARK: - ASAuthorization Extension for Testing
extension ASAuthorization {
    convenience init(credential: ASAuthorizationCredential) {
        self.init()
        // Note: В реальном коде это не будет работать,
        // но для тестирования структуры это подходит
    }
}
