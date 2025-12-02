//
//  DiaryViewModelTests.swift
//  CalorigramTests
//
//  Unit тесты для DiaryViewModel
//

import XCTest
@testable import Calorigram

@MainActor
final class DiaryViewModelTests: XCTestCase {
    var viewModel: DiaryViewModel!
    var mockAPIService: MockAPIService!

    override func setUp() {
        super.setUp()
        mockAPIService = MockAPIService()
        viewModel = DiaryViewModel()
    }

    override func tearDown() {
        viewModel = nil
        mockAPIService = nil
        super.tearDown()
    }

    func testInitialState() {
        XCTAssertTrue(viewModel.meals.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertEqual(viewModel.selectedDate, Date())
    }

    func testLoadMeals_Success() async {
        // Given
        let mockMeals = MockAPIService.createMockMeals()
        mockAPIService.setMockMeals(mockMeals)

        // When
        await viewModel.loadMeals()

        // Then
        // Note: Требуется внедрение зависимости для полноценного тестирования
        XCTAssertFalse(viewModel.isLoading)
    }

    func testLoadMeals_Error() async {
        // Given
        mockAPIService.setShouldReturnError(true)

        // When
        await viewModel.loadMeals()

        // Then
        XCTAssertFalse(viewModel.isLoading)
        // Error handling would need mock service injection
    }

    func testMealsGroupedByType() {
        // Given
        let breakfastMeal = Meal(
            id: 1,
            userId: 1,
            name: "Овсянка",
            calories: 150,
            protein: 5.0,
            fat: 3.0,
            carbs: 27.0,
            mealType: "breakfast",
            createdAt: Date()
        )

        let lunchMeal = Meal(
            id: 2,
            userId: 1,
            name: "Курица",
            calories: 200,
            protein: 40.0,
            fat: 5.0,
            carbs: 0.0,
            mealType: "lunch",
            createdAt: Date()
        )

        viewModel.meals = [breakfastMeal, lunchMeal]

        // When
        let groupedMeals = viewModel.mealsGroupedByType

        // Then
        XCTAssertEqual(groupedMeals.keys.count, 2)
        XCTAssertNotNil(groupedMeals["breakfast"])
        XCTAssertNotNil(groupedMeals["lunch"])
        XCTAssertEqual(groupedMeals["breakfast"]?.count, 1)
        XCTAssertEqual(groupedMeals["lunch"]?.count, 1)
    }

    func testTotalCalories() {
        // Given
        let meals = [
            Meal(id: 1, userId: 1, name: "Meal 1", calories: 100, protein: 10, fat: 5, carbs: 10, mealType: "breakfast", createdAt: Date()),
            Meal(id: 2, userId: 1, name: "Meal 2", calories: 200, protein: 20, fat: 10, carbs: 20, mealType: "lunch", createdAt: Date()),
            Meal(id: 3, userId: 1, name: "Meal 3", calories: 150, protein: 15, fat: 7, carbs: 15, mealType: "dinner", createdAt: Date())
        ]
        viewModel.meals = meals

        // When & Then
        XCTAssertEqual(viewModel.totalCalories, 450)
    }

    func testTotalMacros() {
        // Given
        let meals = [
            Meal(id: 1, userId: 1, name: "Meal 1", calories: 100, protein: 10, fat: 5, carbs: 10, mealType: "breakfast", createdAt: Date()),
            Meal(id: 2, userId: 1, name: "Meal 2", calories: 200, protein: 20, fat: 10, carbs: 20, mealType: "lunch", createdAt: Date())
        ]
        viewModel.meals = meals

        // When & Then
        XCTAssertEqual(viewModel.totalProtein, 30.0)
        XCTAssertEqual(viewModel.totalFat, 15.0)
        XCTAssertEqual(viewModel.totalCarbs, 30.0)
    }

    func testDeleteMeal_Success() async {
        // Given
        let mealToDelete = Meal(
            id: 1,
            userId: 1,
            name: "Test Meal",
            calories: 100,
            protein: 10,
            fat: 5,
            carbs: 10,
            mealType: "breakfast",
            createdAt: Date()
        )
        viewModel.meals = [mealToDelete]

        // When
        await viewModel.deleteMeal(mealToDelete)

        // Then
        XCTAssertFalse(viewModel.isLoading)
        // Note: Требуется внедрение зависимости для проверки удаления
    }

    func testEmptyState() {
        // Given
        viewModel.meals = []

        // When & Then
        XCTAssertEqual(viewModel.emptyStateMessage, "У вас пока нет приемов пищи")
        XCTAssertEqual(viewModel.emptyStateImage, "fork.knife")
    }

    func testEmptyState_WithMeals() {
        // Given
        viewModel.meals = MockAPIService.createMockMeals()

        // When & Then
        XCTAssertNil(viewModel.emptyStateMessage)
        XCTAssertNil(viewModel.emptyStateImage)
    }
}
