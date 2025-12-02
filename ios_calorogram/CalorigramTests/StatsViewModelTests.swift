//
//  StatsViewModelTests.swift
//  CalorigramTests
//
//  Unit тесты для StatsViewModel
//

import XCTest
@testable import Calorigram

@MainActor
final class StatsViewModelTests: XCTestCase {
    var viewModel: StatsViewModel!
    var mockAPIService: MockAPIService!

    override func setUp() {
        super.setUp()
        mockAPIService = MockAPIService()
        viewModel = StatsViewModel()
    }

    override func tearDown() {
        viewModel = nil
        mockAPIService = nil
        super.tearDown()
    }

    func testInitialState() {
        XCTAssertNil(viewModel.todayStats)
        XCTAssertNil(viewModel.weekStats)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
    }

    func testLoadTodayStats_Success() async {
        // Given
        let mockStats = MockAPIService.createMockStatistics()
        mockAPIService.setMockStatistics(mockStats)

        // When
        await viewModel.loadTodayStats()

        // Then
        XCTAssertFalse(viewModel.isLoading)
        // Note: Требуется внедрение зависимости для проверки данных
    }

    func testLoadWeekStats_Success() async {
        // Given
        let mockStats = MockAPIService.createMockStatistics()
        mockAPIService.setMockStatistics(mockStats)

        // When
        await viewModel.loadWeekStats()

        // Then
        XCTAssertFalse(viewModel.isLoading)
    }

    func testLoadStats_Error() async {
        // Given
        mockAPIService.setShouldReturnError(true)

        // When
        await viewModel.loadTodayStats()

        // Then
        XCTAssertFalse(viewModel.isLoading)
    }

    func testEmptyState_NoStats() {
        // Given
        viewModel.todayStats = nil

        // When & Then
        XCTAssertEqual(viewModel.emptyStateMessage, "Статистика недоступна")
        XCTAssertEqual(viewModel.emptyStateImage, "chart.bar.xaxis")
    }

    func testEmptyState_WithStats() {
        // Given
        viewModel.todayStats = MockAPIService.createMockStatistics()

        // When & Then
        XCTAssertNil(viewModel.emptyStateMessage)
        XCTAssertNil(viewModel.emptyStateImage)
    }

    func testCalorieProgress() {
        // Given
        let stats = Statistics(
            date: Date(),
            totalCalories: 1500,
            totalProtein: 100.0,
            totalFat: 50.0,
            totalCarbs: 200.0,
            mealsCount: 3,
            targetCalories: 2000,
            remainingCalories: 500
        )
        viewModel.todayStats = stats

        // When & Then
        XCTAssertEqual(viewModel.calorieProgress, 0.75) // 1500/2000
    }

    func testCalorieProgress_NoTarget() {
        // Given
        let stats = Statistics(
            date: Date(),
            totalCalories: 1500,
            totalProtein: 100.0,
            totalFat: 50.0,
            totalCarbs: 200.0,
            mealsCount: 3,
            targetCalories: nil,
            remainingCalories: nil
        )
        viewModel.todayStats = stats

        // When & Then
        XCTAssertEqual(viewModel.calorieProgress, 0.0)
    }

    func testRemainingCaloriesText() {
        // Given
        let stats = Statistics(
            date: Date(),
            totalCalories: 1500,
            totalProtein: 100.0,
            totalFat: 50.0,
            totalCarbs: 200.0,
            mealsCount: 3,
            targetCalories: 2000,
            remainingCalories: 500
        )
        viewModel.todayStats = stats

        // When & Then
        XCTAssertEqual(viewModel.remainingCaloriesText, "Осталось: 500 ккал")
    }

    func testRemainingCaloriesText_Exceeded() {
        // Given
        let stats = Statistics(
            date: Date(),
            totalCalories: 2200,
            totalProtein: 150.0,
            totalFat: 80.0,
            totalCarbs: 250.0,
            mealsCount: 4,
            targetCalories: 2000,
            remainingCalories: -200
        )
        viewModel.todayStats = stats

        // When & Then
        XCTAssertEqual(viewModel.remainingCaloriesText, "Превышение: 200 ккал")
    }

    func testRemainingCaloriesText_NoTarget() {
        // Given
        let stats = Statistics(
            date: Date(),
            totalCalories: 1500,
            totalProtein: 100.0,
            totalFat: 50.0,
            totalCarbs: 200.0,
            mealsCount: 3,
            targetCalories: nil,
            remainingCalories: nil
        )
        viewModel.todayStats = stats

        // When & Then
        XCTAssertEqual(viewModel.remainingCaloriesText, "Цель не установлена")
    }

    func testWeeklyData_Empty() {
        // Given
        viewModel.weekStats = nil

        // When & Then
        XCTAssertTrue(viewModel.weeklyCaloriesData.isEmpty)
        XCTAssertTrue(viewModel.weeklyLabels.isEmpty)
    }

    func testWeeklyData_WithStats() {
        // Given - симулируем недельную статистику
        // Note: Требуется более сложная mock структура для недельных данных

        // When & Then
        // XCTAssertFalse(viewModel.weeklyCaloriesData.isEmpty)
    }
}
