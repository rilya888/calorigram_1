//
//  MockAPIService.swift
//  CalorigramTests
//
//  Mock сервис для тестирования
//

import Foundation
@testable import Calorigram

class MockAPIService: APIServiceProtocol {
    // MARK: - Properties
    var shouldReturnError = false
    var mockUser: User?
    var mockMeals: [Meal] = []
    var mockStatistics: Statistics?
    var mockSubscription: Subscription?
    var delay: TimeInterval = 0

    // MARK: - Initialization
    init() {}

    // MARK: - Mock Control Methods
    func setShouldReturnError(_ error: Bool) {
        shouldReturnError = error
    }

    func setMockUser(_ user: User?) {
        mockUser = user
    }

    func setMockMeals(_ meals: [Meal]) {
        mockMeals = meals
    }

    func setMockStatistics(_ stats: Statistics?) {
        mockStatistics = stats
    }

    func setDelay(_ delay: TimeInterval) {
        self.delay = delay
    }

    // MARK: - APIServiceProtocol Implementation

    func request<T: Decodable>(
        endpoint: String,
        method: String,
        body: Encodable?,
        headers: [String: String]?,
        retryCount: Int,
        retryDelay: TimeInterval
    ) async throws -> T {
        // Simulate network delay
        if delay > 0 {
            try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
        }

        if shouldReturnError {
            throw APIError.serverError(500, "Mock error")
        }

        // Return mock data based on endpoint
        switch endpoint {
        case Constants.API.profileMe:
            if let user = mockUser as? T {
                return user
            }
        case Constants.API.meals:
            if let meals = mockMeals as? T {
                return meals
            }
        case Constants.API.mealsToday:
            if let meals = mockMeals as? T {
                return meals
            }
        case Constants.API.statisticsToday:
            if let stats = mockStatistics as? T {
                return stats
            }
        case Constants.API.statisticsWeek:
            if let stats = mockStatistics as? T {
                return stats
            }
        default:
            break
        }

        throw APIError.invalidResponse
    }

    func request(
        endpoint: String,
        method: String,
        body: Encodable?,
        headers: [String: String]?,
        retryCount: Int,
        retryDelay: TimeInterval
    ) async throws {
        if delay > 0 {
            try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
        }

        if shouldReturnError {
            throw APIError.serverError(500, "Mock error")
        }
    }
}

// MARK: - Test Data Helpers
extension MockAPIService {
    static func createMockUser() -> User {
        User(
            id: 1,
            telegramId: nil,
            email: "test@example.com",
            name: "Test User",
            gender: "Мужской",
            age: 30,
            height: 175.0,
            weight: 75.0,
            activityLevel: "Умеренная",
            goal: "Похудеть",
            dailyCalories: 2500,
            targetCalories: 2200,
            targetProtein: 165.0,
            targetFat: 73.0,
            targetCarbs: 275.0,
            subscriptionType: "premium",
            subscriptionExpiresAt: nil,
            isPremium: true
        )
    }

    static func createMockMeals() -> [Meal] {
        [
            Meal(
                id: 1,
                userId: 1,
                name: "Овсяная каша",
                calories: 150,
                protein: 5.0,
                fat: 3.0,
                carbs: 27.0,
                mealType: "breakfast",
                createdAt: Date()
            ),
            Meal(
                id: 2,
                userId: 1,
                name: "Куриная грудка",
                calories: 165,
                protein: 31.0,
                fat: 3.6,
                carbs: 0.0,
                mealType: "lunch",
                createdAt: Date()
            )
        ]
    }

    static func createMockStatistics() -> Statistics {
        Statistics(
            date: Date(),
            totalCalories: 500,
            totalProtein: 40.0,
            totalFat: 15.0,
            totalCarbs: 50.0,
            mealsCount: 2,
            targetCalories: 2000,
            remainingCalories: 1500
        )
    }
}
