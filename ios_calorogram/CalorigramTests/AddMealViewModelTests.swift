//
//  AddMealViewModelTests.swift
//  CalorigramTests
//
//  Unit тесты для AddMealViewModel
//

import XCTest
@testable import Calorigram

@MainActor
final class AddMealViewModelTests: XCTestCase {
    var viewModel: AddMealViewModel!
    var mockAPIService: MockAPIService!

    override func setUp() {
        super.setUp()
        mockAPIService = MockAPIService()
        viewModel = AddMealViewModel()
    }

    override func tearDown() {
        viewModel = nil
        mockAPIService = nil
        super.tearDown()
    }

    func testInitialState() {
        XCTAssertEqual(viewModel.name, "")
        XCTAssertEqual(viewModel.calories, 0)
        XCTAssertEqual(viewModel.protein, 0.0)
        XCTAssertEqual(viewModel.fat, 0.0)
        XCTAssertEqual(viewModel.carbs, 0.0)
        XCTAssertEqual(viewModel.weight, 0.0)
        XCTAssertEqual(viewModel.selectedMealType, "breakfast")
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertFalse(viewModel.showSuccessMessage)
    }

    func testMealTypeOptions() {
        let expectedTypes = [
            "breakfast": "Завтрак",
            "lunch": "Обед",
            "dinner": "Ужин",
            "snack": "Перекус"
        ]

        for (key, value) in expectedTypes {
            XCTAssertEqual(viewModel.mealTypeDisplayName(for: key), value)
        }
    }

    func testFormValidation_ValidData() {
        // Given
        viewModel.name = "Куриная грудка"
        viewModel.calories = 165
        viewModel.protein = 31.0
        viewModel.fat = 3.6
        viewModel.carbs = 0.0
        viewModel.weight = 150.0

        // When & Then
        XCTAssertTrue(viewModel.isFormValid)
    }

    func testFormValidation_EmptyName() {
        // Given
        viewModel.name = ""
        viewModel.calories = 100
        viewModel.protein = 10.0

        // When & Then
        XCTAssertFalse(viewModel.isFormValid)
    }

    func testFormValidation_ZeroCalories() {
        // Given
        viewModel.name = "Вода"
        viewModel.calories = 0
        viewModel.protein = 0.0

        // When & Then
        XCTAssertFalse(viewModel.isFormValid)
    }

    func testFormValidation_NegativeValues() {
        // Given
        viewModel.name = "Test Meal"
        viewModel.calories = -100
        viewModel.protein = -10.0

        // When & Then
        XCTAssertFalse(viewModel.isFormValid)
    }

    func testAddMeal_Success() async {
        // Given
        setupValidMealData()

        // When
        await viewModel.addMeal()

        // Then
        XCTAssertFalse(viewModel.isLoading)
        // Note: Требуется внедрение зависимости для проверки сохранения
    }

    func testAddMeal_ValidationFailure() async {
        // Given
        viewModel.name = "" // Invalid
        viewModel.calories = 100

        // When
        await viewModel.addMeal()

        // Then
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertFalse(viewModel.showSuccessMessage)
    }

    func testAddMeal_NetworkError() async {
        // Given
        setupValidMealData()
        mockAPIService.setShouldReturnError(true)

        // When
        await viewModel.addMeal()

        // Then
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertFalse(viewModel.showSuccessMessage)
    }

    func testResetForm() {
        // Given
        setupValidMealData()
        viewModel.errorMessage = "Some error"
        viewModel.showSuccessMessage = true

        // When
        viewModel.resetForm()

        // Then
        XCTAssertEqual(viewModel.name, "")
        XCTAssertEqual(viewModel.calories, 0)
        XCTAssertEqual(viewModel.protein, 0.0)
        XCTAssertEqual(viewModel.fat, 0.0)
        XCTAssertEqual(viewModel.carbs, 0.0)
        XCTAssertEqual(viewModel.weight, 0.0)
        XCTAssertEqual(viewModel.selectedMealType, "breakfast")
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertFalse(viewModel.showSuccessMessage)
    }

    func testCaloriesFromMacros() {
        // Given
        viewModel.protein = 20.0  // 20 * 4 = 80 калорий
        viewModel.fat = 10.0      // 10 * 9 = 90 калорий
        viewModel.carbs = 15.0    // 15 * 4 = 60 калорий
        // Итого: 80 + 90 + 60 = 230 калорий

        // When & Then
        XCTAssertEqual(viewModel.caloriesFromMacros, 230)
    }

    func testCaloriesFromMacros_ZeroValues() {
        // Given
        viewModel.protein = 0.0
        viewModel.fat = 0.0
        viewModel.carbs = 0.0

        // When & Then
        XCTAssertEqual(viewModel.caloriesFromMacros, 0)
    }

    func testMacrosConsistency() {
        // Given
        viewModel.protein = 25.0
        viewModel.fat = 15.0
        viewModel.carbs = 50.0
        viewModel.calories = 415 // Правильное значение: (25*4) + (15*9) + (50*4) = 100 + 135 + 200 = 435

        // When & Then
        XCTAssertFalse(viewModel.areMacrosConsistent) // 415 != 435
    }

    func testMacrosConsistency_Consistent() {
        // Given
        viewModel.protein = 25.0  // 100 калорий
        viewModel.fat = 15.0      // 135 калорий
        viewModel.carbs = 50.0    // 200 калорий
        viewModel.calories = 435  // 100 + 135 + 200

        // When & Then
        XCTAssertTrue(viewModel.areMacrosConsistent)
    }

    func testMealTypeSelection() {
        let mealTypes = ["breakfast", "lunch", "dinner", "snack"]

        for mealType in mealTypes {
            viewModel.selectedMealType = mealType
            XCTAssertEqual(viewModel.selectedMealType, mealType)
        }
    }

    // MARK: - Helper Methods

    private func setupValidMealData() {
        viewModel.name = "Куриная грудка"
        viewModel.calories = 165
        viewModel.protein = 31.0
        viewModel.fat = 3.6
        viewModel.carbs = 0.0
        viewModel.weight = 150.0
        viewModel.selectedMealType = "lunch"
    }

    // MARK: - Validation Tests

    func testNameValidation() {
        // Valid names
        let validNames = ["Курица", "Овсяная каша", "Стейк с овощами", "Йогурт"]
        for name in validNames {
            viewModel.name = name
            XCTAssertTrue(viewModel.isNameValid, "Name should be valid: \(name)")
        }

        // Invalid names
        let invalidNames = ["", "   ", "\n\t"]
        for name in invalidNames {
            viewModel.name = name
            XCTAssertFalse(viewModel.isNameValid, "Name should be invalid: \(name)")
        }
    }

    func testCaloriesValidation() {
        // Valid calories
        let validCalories = [1, 100, 500, 2000]
        for calories in validCalories {
            viewModel.calories = calories
            XCTAssertTrue(viewModel.areCaloriesValid, "Calories should be valid: \(calories)")
        }

        // Invalid calories
        let invalidCalories = [0, -100, -1]
        for calories in invalidCalories {
            viewModel.calories = calories
            XCTAssertFalse(viewModel.areCaloriesValid, "Calories should be invalid: \(calories)")
        }
    }

    func testMacrosValidation() {
        // Valid macros
        let validMacros: [(Double, Double, Double)] = [
            (10.0, 5.0, 20.0),
            (0.0, 0.0, 0.0),
            (50.0, 30.0, 100.0)
        ]

        for (protein, fat, carbs) in validMacros {
            viewModel.protein = protein
            viewModel.fat = fat
            viewModel.carbs = carbs
            XCTAssertTrue(viewModel.areMacrosValid, "Macros should be valid: P\(protein) F\(fat) C\(carbs)")
        }

        // Invalid macros
        let invalidMacros: [(Double, Double, Double)] = [
            (-5.0, 10.0, 20.0),
            (10.0, -5.0, 20.0),
            (10.0, 5.0, -5.0)
        ]

        for (protein, fat, carbs) in invalidMacros {
            viewModel.protein = protein
            viewModel.fat = fat
            viewModel.carbs = carbs
            XCTAssertFalse(viewModel.areMacrosValid, "Macros should be invalid: P\(protein) F\(fat) C\(carbs)")
        }
    }

    // MARK: - Performance Tests

    func testPerformance_FormValidation() {
        setupValidMealData()

        measure {
            for _ in 0..<1000 {
                let _ = viewModel.isFormValid
            }
        }
    }

    func testPerformance_MacrosCalculation() {
        viewModel.protein = 25.0
        viewModel.fat = 15.0
        viewModel.carbs = 50.0

        measure {
            for _ in 0..<1000 {
                let _ = viewModel.caloriesFromMacros
            }
        }
    }
}
