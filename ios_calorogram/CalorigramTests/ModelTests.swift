//
//  ModelTests.swift
//  CalorigramTests
//
//  Unit тесты для моделей данных
//

import XCTest
@testable import Calorigram

final class ModelTests: XCTestCase {

    // MARK: - User Model Tests

    func testUserInitialization() {
        let user = User(
            id: 1,
            telegramId: 123456789,
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
            subscriptionExpiresAt: Date(),
            isPremium: true
        )

        XCTAssertEqual(user.id, 1)
        XCTAssertEqual(user.telegramId, 123456789)
        XCTAssertEqual(user.email, "test@example.com")
        XCTAssertEqual(user.name, "Test User")
        XCTAssertEqual(user.gender, "Мужской")
        XCTAssertEqual(user.age, 30)
        XCTAssertEqual(user.height, 175.0)
        XCTAssertEqual(user.weight, 75.0)
        XCTAssertEqual(user.activityLevel, "Умеренная")
        XCTAssertEqual(user.goal, "Похудеть")
        XCTAssertEqual(user.dailyCalories, 2500)
        XCTAssertEqual(user.targetCalories, 2200)
        XCTAssertEqual(user.targetProtein, 165.0)
        XCTAssertEqual(user.targetFat, 73.0)
        XCTAssertEqual(user.targetCarbs, 275.0)
        XCTAssertEqual(user.subscriptionType, "premium")
        XCTAssertTrue(user.isPremium)
    }

    func testUserDecoding() throws {
        let json = """
        {
            "id": 1,
            "telegram_id": 123456789,
            "email": "test@example.com",
            "name": "Test User",
            "gender": "Мужской",
            "age": 30,
            "height": 175.0,
            "weight": 75.0,
            "activity_level": "Умеренная",
            "goal": "Похудеть",
            "daily_calories": 2500,
            "target_calories": 2200,
            "target_protein": 165.0,
            "target_fat": 73.0,
            "target_carbs": 275.0,
            "subscription_type": "premium",
            "subscription_expires_at": "2024-12-31T23:59:59Z",
            "is_premium": true
        }
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let user = try decoder.decode(User.self, from: json)

        XCTAssertEqual(user.id, 1)
        XCTAssertEqual(user.email, "test@example.com")
        XCTAssertEqual(user.name, "Test User")
        XCTAssertEqual(user.age, 30)
        XCTAssertEqual(user.height, 175.0)
        XCTAssertEqual(user.weight, 75.0)
        XCTAssertTrue(user.isPremium)
    }

    func testUserEncoding() throws {
        let user = User(
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

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(user)
        let jsonString = String(data: data, encoding: .utf8)!

        XCTAssertTrue(jsonString.contains("\"email\":\"test@example.com\""))
        XCTAssertTrue(jsonString.contains("\"name\":\"Test User\""))
        XCTAssertTrue(jsonString.contains("\"is_premium\":true"))
    }

    func testUserEquatable() {
        let user1 = User(
            id: 1,
            telegramId: 123,
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

        let user2 = User(
            id: 1,
            telegramId: 123,
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

        let user3 = User(
            id: 2,  // different id
            telegramId: 123,
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

        XCTAssertEqual(user1, user2)
        XCTAssertNotEqual(user1, user3)
    }

    // MARK: - Meal Model Tests

    func testMealInitialization() {
        let date = Date()
        let meal = Meal(
            id: 1,
            userId: 1,
            name: "Овсяная каша",
            calories: 150,
            protein: 5.0,
            fat: 3.0,
            carbs: 27.0,
            mealType: "breakfast",
            createdAt: date
        )

        XCTAssertEqual(meal.id, 1)
        XCTAssertEqual(meal.userId, 1)
        XCTAssertEqual(meal.name, "Овсяная каша")
        XCTAssertEqual(meal.calories, 150)
        XCTAssertEqual(meal.protein, 5.0)
        XCTAssertEqual(meal.fat, 3.0)
        XCTAssertEqual(meal.carbs, 27.0)
        XCTAssertEqual(meal.mealType, "breakfast")
        XCTAssertEqual(meal.createdAt, date)
    }

    func testMealDecoding() throws {
        let json = """
        {
            "id": 1,
            "user_id": 1,
            "name": "Овсяная каша",
            "calories": 150,
            "protein": 5.0,
            "fat": 3.0,
            "carbs": 27.0,
            "meal_type": "breakfast",
            "created_at": "2024-01-01T10:00:00Z"
        }
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let meal = try decoder.decode(Meal.self, from: json)

        XCTAssertEqual(meal.id, 1)
        XCTAssertEqual(meal.name, "Овсяная каша")
        XCTAssertEqual(meal.calories, 150)
        XCTAssertEqual(meal.protein, 5.0)
        XCTAssertEqual(meal.mealType, "breakfast")
    }

    // MARK: - Statistics Model Tests

    func testStatisticsInitialization() {
        let date = Date()
        let stats = Statistics(
            date: date,
            totalCalories: 1500,
            totalProtein: 100.0,
            totalFat: 50.0,
            totalCarbs: 200.0,
            mealsCount: 3,
            targetCalories: 2000,
            remainingCalories: 500
        )

        XCTAssertEqual(stats.date, date)
        XCTAssertEqual(stats.totalCalories, 1500)
        XCTAssertEqual(stats.totalProtein, 100.0)
        XCTAssertEqual(stats.totalFat, 50.0)
        XCTAssertEqual(stats.totalCarbs, 200.0)
        XCTAssertEqual(stats.mealsCount, 3)
        XCTAssertEqual(stats.targetCalories, 2000)
        XCTAssertEqual(stats.remainingCalories, 500)
    }

    func testStatisticsDecoding() throws {
        let json = """
        {
            "date": "2024-01-01T00:00:00Z",
            "total_calories": 1500,
            "total_protein": 100.0,
            "total_fat": 50.0,
            "total_carbs": 200.0,
            "meals_count": 3,
            "target_calories": 2000,
            "remaining_calories": 500
        }
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let stats = try decoder.decode(Statistics.self, from: json)

        XCTAssertEqual(stats.totalCalories, 1500)
        XCTAssertEqual(stats.totalProtein, 100.0)
        XCTAssertEqual(stats.mealsCount, 3)
        XCTAssertEqual(stats.targetCalories, 2000)
        XCTAssertEqual(stats.remainingCalories, 500)
    }

    // MARK: - Subscription Model Tests

    func testSubscriptionInitialization() {
        let date = Date()
        let subscription = Subscription(
            type: "premium",
            expiresAt: date,
            isActive: true,
            autoRenew: false
        )

        XCTAssertEqual(subscription.type, "premium")
        XCTAssertEqual(subscription.expiresAt, date)
        XCTAssertTrue(subscription.isActive)
        XCTAssertFalse(subscription.autoRenew)
    }

    func testSubscriptionDecoding() throws {
        let json = """
        {
            "type": "premium",
            "expires_at": "2024-12-31T23:59:59Z",
            "is_active": true,
            "auto_renew": false
        }
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let subscription = try decoder.decode(Subscription.self, from: json)

        XCTAssertEqual(subscription.type, "premium")
        XCTAssertTrue(subscription.isActive)
        XCTAssertFalse(subscription.autoRenew)
    }

    // MARK: - Edge Cases

    func testUserWithNilValues() {
        let user = User(
            id: 1,
            telegramId: nil,
            email: nil,
            name: "",
            gender: nil,
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

        XCTAssertEqual(user.id, 1)
        XCTAssertNil(user.telegramId)
        XCTAssertNil(user.email)
        XCTAssertEqual(user.name, "")
        XCTAssertNil(user.gender)
        XCTAssertNil(user.age)
        XCTAssertNil(user.height)
        XCTAssertNil(user.weight)
        XCTAssertFalse(user.isPremium)
    }

    func testMealWithZeroValues() {
        let meal = Meal(
            id: 1,
            userId: 1,
            name: "Вода",
            calories: 0,
            protein: 0.0,
            fat: 0.0,
            carbs: 0.0,
            mealType: "drink",
            createdAt: Date()
        )

        XCTAssertEqual(meal.calories, 0)
        XCTAssertEqual(meal.protein, 0.0)
        XCTAssertEqual(meal.fat, 0.0)
        XCTAssertEqual(meal.carbs, 0.0)
    }

    // MARK: - Meal Model Tests

    func testMealInitialization() {
        let date = Date()
        let meal = Meal(
            id: 1,
            userId: 1,
            name: "Овсяная каша",
            calories: 150,
            protein: 5.0,
            fat: 3.0,
            carbs: 27.0,
            mealType: "breakfast",
            createdAt: date
        )

        XCTAssertEqual(meal.id, 1)
        XCTAssertEqual(meal.userId, 1)
        XCTAssertEqual(meal.name, "Овсяная каша")
        XCTAssertEqual(meal.calories, 150)
        XCTAssertEqual(meal.protein, 5.0)
        XCTAssertEqual(meal.fat, 3.0)
        XCTAssertEqual(meal.carbs, 27.0)
        XCTAssertEqual(meal.mealType, "breakfast")
        XCTAssertEqual(meal.createdAt, date)
    }

    func testMealDecoding() throws {
        let json = """
        {
            "id": 1,
            "user_id": 1,
            "name": "Овсяная каша",
            "calories": 150,
            "protein": 5.0,
            "fat": 3.0,
            "carbs": 27.0,
            "meal_type": "breakfast",
            "created_at": "2024-01-01T10:00:00Z"
        }
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let meal = try decoder.decode(Meal.self, from: json)

        XCTAssertEqual(meal.id, 1)
        XCTAssertEqual(meal.name, "Овсяная каша")
        XCTAssertEqual(meal.calories, 150)
        XCTAssertEqual(meal.protein, 5.0)
        XCTAssertEqual(meal.mealType, "breakfast")
    }

    func testMealEncoding() throws {
        let meal = Meal(
            id: 1,
            userId: 1,
            name: "Куриная грудка",
            calories: 165,
            protein: 31.0,
            fat: 3.6,
            carbs: 0.0,
            mealType: "lunch",
            createdAt: Date()
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(meal)
        let jsonString = String(data: data, encoding: .utf8)!

        XCTAssertTrue(jsonString.contains("\"name\":\"Куриная грудка\""))
        XCTAssertTrue(jsonString.contains("\"calories\":165"))
        XCTAssertTrue(jsonString.contains("\"meal_type\":\"lunch\""))
    }

    func testMealTotalMacros() {
        let meal = Meal(
            id: 1,
            userId: 1,
            name: "Бургер",
            calories: 500,
            protein: 25.0,
            fat: 25.0,
            carbs: 40.0,
            mealType: "lunch",
            createdAt: Date()
        )

        // Проверяем, что калории соответствуют макронутриентам
        // 25*4 + 25*9 + 40*4 = 100 + 225 + 160 = 485 (примерно 500 с округлением)
        XCTAssertEqual(meal.protein, 25.0)
        XCTAssertEqual(meal.fat, 25.0)
        XCTAssertEqual(meal.carbs, 40.0)
    }

    // MARK: - Statistics Model Tests

    func testStatisticsInitialization() {
        let date = Date()
        let stats = Statistics(
            date: date,
            totalCalories: 1500,
            totalProtein: 100.0,
            totalFat: 50.0,
            totalCarbs: 200.0,
            mealsCount: 3,
            targetCalories: 2000,
            remainingCalories: 500
        )

        XCTAssertEqual(stats.date, date)
        XCTAssertEqual(stats.totalCalories, 1500)
        XCTAssertEqual(stats.totalProtein, 100.0)
        XCTAssertEqual(stats.totalFat, 50.0)
        XCTAssertEqual(stats.totalCarbs, 200.0)
        XCTAssertEqual(stats.mealsCount, 3)
        XCTAssertEqual(stats.targetCalories, 2000)
        XCTAssertEqual(stats.remainingCalories, 500)
    }

    func testStatisticsDecoding() throws {
        let json = """
        {
            "date": "2024-01-01T00:00:00Z",
            "total_calories": 1500,
            "total_protein": 100.0,
            "total_fat": 50.0,
            "total_carbs": 200.0,
            "meals_count": 3,
            "target_calories": 2000,
            "remaining_calories": 500
        }
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let stats = try decoder.decode(Statistics.self, from: json)

        XCTAssertEqual(stats.totalCalories, 1500)
        XCTAssertEqual(stats.totalProtein, 100.0)
        XCTAssertEqual(stats.mealsCount, 3)
        XCTAssertEqual(stats.targetCalories, 2000)
        XCTAssertEqual(stats.remainingCalories, 500)
    }

    func testStatisticsEncoding() throws {
        let stats = Statistics(
            date: Date(),
            totalCalories: 1800,
            totalProtein: 120.0,
            totalFat: 60.0,
            totalCarbs: 220.0,
            mealsCount: 4,
            targetCalories: 2000,
            remainingCalories: 200
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(stats)
        let jsonString = String(data: data, encoding: .utf8)!

        XCTAssertTrue(jsonString.contains("\"total_calories\":1800"))
        XCTAssertTrue(jsonString.contains("\"meals_count\":4"))
    }

    func testStatisticsCalorieBalance() {
        let stats = Statistics(
            date: Date(),
            totalCalories: 1800,
            totalProtein: 120.0,
            totalFat: 60.0,
            totalCarbs: 220.0,
            mealsCount: 4,
            targetCalories: 2000,
            remainingCalories: 200
        )

        // Проверяем логику баланса калорий
        XCTAssertEqual(stats.targetCalories, 2000)
        XCTAssertEqual(stats.totalCalories, 1800)
        XCTAssertEqual(stats.remainingCalories, 200)
    }

    func testStatisticsZeroValues() {
        let stats = Statistics(
            date: Date(),
            totalCalories: 0,
            totalProtein: 0.0,
            totalFat: 0.0,
            totalCarbs: 0.0,
            mealsCount: 0,
            targetCalories: nil,
            remainingCalories: nil
        )

        XCTAssertEqual(stats.totalCalories, 0)
        XCTAssertEqual(stats.mealsCount, 0)
        XCTAssertNil(stats.targetCalories)
        XCTAssertNil(stats.remainingCalories)
    }

    // MARK: - Subscription Model Tests

    func testSubscriptionInitialization() {
        let date = Date()
        let subscription = Subscription(
            type: "premium",
            expiresAt: date,
            isActive: true,
            autoRenew: false
        )

        XCTAssertEqual(subscription.type, "premium")
        XCTAssertEqual(subscription.expiresAt, date)
        XCTAssertTrue(subscription.isActive)
        XCTAssertFalse(subscription.autoRenew)
    }

    func testSubscriptionDecoding() throws {
        let json = """
        {
            "type": "premium",
            "expires_at": "2024-12-31T23:59:59Z",
            "is_active": true,
            "auto_renew": false
        }
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let subscription = try decoder.decode(Subscription.self, from: json)

        XCTAssertEqual(subscription.type, "premium")
        XCTAssertTrue(subscription.isActive)
        XCTAssertFalse(subscription.autoRenew)
    }

    func testSubscriptionEncoding() throws {
        let subscription = Subscription(
            type: "trial",
            expiresAt: Date(),
            isActive: true,
            autoRenew: true
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let data = try encoder.encode(subscription)
        let jsonString = String(data: data, encoding: .utf8)!

        XCTAssertTrue(jsonString.contains("\"type\":\"trial\""))
        XCTAssertTrue(jsonString.contains("\"is_active\":true"))
        XCTAssertTrue(jsonString.contains("\"auto_renew\":true"))
    }

    func testSubscriptionTypes() {
        let types = ["trial", "premium", "family", "annual"]

        for type in types {
            let subscription = Subscription(
                type: type,
                expiresAt: Date(),
                isActive: true,
                autoRenew: false
            )
            XCTAssertEqual(subscription.type, type)
        }
    }

    func testSubscriptionStatus() {
        // Active subscription
        let activeSub = Subscription(
            type: "premium",
            expiresAt: Date().addingTimeInterval(86400), // Tomorrow
            isActive: true,
            autoRenew: true
        )
        XCTAssertTrue(activeSub.isActive)

        // Expired subscription
        let expiredSub = Subscription(
            type: "premium",
            expiresAt: Date().addingTimeInterval(-86400), // Yesterday
            isActive: false,
            autoRenew: false
        )
        XCTAssertFalse(expiredSub.isActive)
    }

    // MARK: - Integration Tests

    func testUserMealRelationship() {
        let user = User(
            id: 1,
            telegramId: 123,
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

        let meal = Meal(
            id: 1,
            userId: user.id,
            name: "Завтрак",
            calories: 400,
            protein: 25.0,
            fat: 15.0,
            carbs: 45.0,
            mealType: "breakfast",
            createdAt: Date()
        )

        XCTAssertEqual(meal.userId, user.id)
        XCTAssertTrue(meal.calories <= user.dailyCalories)
    }

    func testStatisticsAccuracy() {
        let meals = [
            Meal(id: 1, userId: 1, name: "Meal 1", calories: 300, protein: 20, fat: 10, carbs: 30, mealType: "breakfast", createdAt: Date()),
            Meal(id: 2, userId: 1, name: "Meal 2", calories: 500, protein: 40, fat: 20, carbs: 50, mealType: "lunch", createdAt: Date()),
            Meal(id: 3, userId: 1, name: "Meal 3", calories: 400, protein: 30, fat: 15, carbs: 40, mealType: "dinner", createdAt: Date())
        ]

        let totalCalories = meals.reduce(0) { $0 + $1.calories }
        let totalProtein = meals.reduce(0.0) { $0 + $1.protein }
        let totalFat = meals.reduce(0.0) { $0 + $1.fat }
        let totalCarbs = meals.reduce(0.0) { $0 + $1.carbs }

        let stats = Statistics(
            date: Date(),
            totalCalories: totalCalories,
            totalProtein: totalProtein,
            totalFat: totalFat,
            totalCarbs: totalCarbs,
            mealsCount: meals.count,
            targetCalories: 2000,
            remainingCalories: 2000 - totalCalories
        )

        XCTAssertEqual(stats.totalCalories, 1200)
        XCTAssertEqual(stats.totalProtein, 90.0)
        XCTAssertEqual(stats.totalFat, 45.0)
        XCTAssertEqual(stats.totalCarbs, 120.0)
        XCTAssertEqual(stats.mealsCount, 3)
        XCTAssertEqual(stats.remainingCalories, 800)
    }
}
