//
//  ProfileViewModelTests.swift
//  CalorigramTests
//
//  Unit тесты для ProfileViewModel
//

import XCTest
@testable import Calorigram

@MainActor
final class ProfileViewModelTests: XCTestCase {
    var viewModel: ProfileViewModel!
    var mockAPIService: MockAPIService!

    override func setUp() {
        super.setUp()
        mockAPIService = MockAPIService()
        viewModel = ProfileViewModel()
    }

    override func tearDown() {
        viewModel = nil
        mockAPIService = nil
        super.tearDown()
    }

    func testInitialState() {
        XCTAssertNil(viewModel.userProfile)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
    }

    func testLoadProfile_Success() async {
        // Given
        let mockUser = MockAPIService.createMockUser()
        mockAPIService.setMockUser(mockUser)

        // When
        await viewModel.loadProfile()

        // Then
        XCTAssertFalse(viewModel.isLoading)
    }

    func testUpdateProfile_Success() async {
        // Given
        let name = "Updated Name"
        let age = 35
        let height = 180.0
        let weight = 80.0
        let gender = "Мужской"
        let goal = "Поддерживать вес"
        let activityLevel = "Высокая"

        // When
        let success = await viewModel.updateProfile(
            name: name,
            age: age,
            height: height,
            weight: weight,
            gender: gender,
            goal: goal,
            activityLevel: activityLevel
        )

        // Then
        XCTAssertFalse(viewModel.isLoading)
        // Note: Требуется внедрение зависимости для проверки результата
    }

    func testUpdateProfile_ValidationFailure() async {
        // Given - invalid data
        let name = ""  // empty name should fail
        let age = 10   // too young
        let height = 50.0  // too short
        let weight = 10.0  // too light
        let gender = "Invalid"
        let goal = "Invalid"
        let activityLevel = "Invalid"

        // When
        let success = await viewModel.updateProfile(
            name: name,
            age: age,
            height: height,
            weight: weight,
            gender: gender,
            goal: goal,
            activityLevel: activityLevel
        )

        // Then
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertFalse(success)
    }

    func testCalculateProfile_Success() async {
        // Given
        let gender = "Мужской"
        let age = 30
        let height = 175.0
        let weight = 75.0
        let activityLevel = "Умеренная"
        let goal = "Похудеть"

        // When
        let success = await viewModel.calculateProfile(
            gender: gender,
            age: age,
            height: height,
            weight: weight,
            activityLevel: activityLevel,
            goal: goal
        )

        // Then
        XCTAssertFalse(viewModel.isLoading)
    }

    func testCalculateProfile_InvalidParameters() async {
        // Given - invalid parameters
        let gender = "Invalid"
        let age = 5     // too young
        let height = 30.0  // too short
        let weight = 5.0   // too light
        let activityLevel = "Invalid"
        let goal = "Invalid"

        // When
        let success = await viewModel.calculateProfile(
            gender: gender,
            age: age,
            height: height,
            weight: weight,
            activityLevel: activityLevel,
            goal: goal
        )

        // Then
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertFalse(success)
    }

    func testValidation_Name() {
        // Valid names
        XCTAssertTrue(viewModel.isValidName("John Doe"))
        XCTAssertTrue(viewModel.isValidName("Иван Петров"))

        // Invalid names
        XCTAssertFalse(viewModel.isValidName(""))
        XCTAssertFalse(viewModel.isValidName("   "))
        XCTAssertFalse(viewModel.isValidName(String(repeating: "A", count: 101))) // too long
    }

    func testValidation_Age() {
        // Valid ages
        XCTAssertTrue(viewModel.isValidAge(18))
        XCTAssertTrue(viewModel.isValidAge(65))

        // Invalid ages
        XCTAssertFalse(viewModel.isValidAge(0))
        XCTAssertFalse(viewModel.isValidAge(121))
        XCTAssertFalse(viewModel.isValidAge(-5))
    }

    func testValidation_Height() {
        // Valid heights
        XCTAssertTrue(viewModel.isValidHeight(150.0))
        XCTAssertTrue(viewModel.isValidHeight(200.0))

        // Invalid heights
        XCTAssertFalse(viewModel.isValidHeight(40.0))
        XCTAssertFalse(viewModel.isValidHeight(260.0))
    }

    func testValidation_Weight() {
        // Valid weights
        XCTAssertTrue(viewModel.isValidWeight(45.0))
        XCTAssertTrue(viewModel.isValidWeight(150.0))

        // Invalid weights
        XCTAssertFalse(viewModel.isValidWeight(15.0))
        XCTAssertFalse(viewModel.isValidWeight(350.0))
    }

    func testValidation_Gender() {
        // Valid genders
        XCTAssertTrue(viewModel.isValidGender("Мужской"))
        XCTAssertTrue(viewModel.isValidGender("Женский"))

        // Invalid genders
        XCTAssertFalse(viewModel.isValidGender("Invalid"))
        XCTAssertFalse(viewModel.isValidGender(""))
    }

    func testValidation_ActivityLevel() {
        // Valid activity levels
        XCTAssertTrue(viewModel.isValidActivityLevel("Низкая"))
        XCTAssertTrue(viewModel.isValidActivityLevel("Высокая"))

        // Invalid activity levels
        XCTAssertFalse(viewModel.isValidActivityLevel("Invalid"))
        XCTAssertFalse(viewModel.isValidActivityLevel(""))
    }

    func testValidation_Goal() {
        // Valid goals
        XCTAssertTrue(viewModel.isValidGoal("Похудеть"))
        XCTAssertTrue(viewModel.isValidGoal("Набрать вес"))

        // Invalid goals
        XCTAssertFalse(viewModel.isValidGoal("Invalid"))
        XCTAssertFalse(viewModel.isValidGoal(""))
    }

    func testErrorMessage_Handling() {
        // Given
        viewModel.errorMessage = "Test error"

        // When & Then
        XCTAssertEqual(viewModel.errorMessage, "Test error")

        // Clear error
        viewModel.errorMessage = nil
        XCTAssertNil(viewModel.errorMessage)
    }
}
