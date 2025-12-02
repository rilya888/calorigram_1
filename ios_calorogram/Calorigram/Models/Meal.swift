//
//  Meal.swift
//  Calorigram
//
//  Модель приема пищи
//

import Foundation

struct Meal: Codable, Identifiable {
    let id: Int?
    let mealType: String
    let mealName: String?
    let dishName: String
    let calories: Int
    let protein: Double
    let fat: Double
    let carbs: Double
    let description: String?
    let weight: Double?
    let time: String?
    let createdAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case mealType = "meal_type"
        case mealName = "meal_name"
        case dishName = "dish_name"
        case calories
        case protein
        case fat
        case carbs
        case description
        case weight
        case time
        case createdAt = "created_at"
    }
}

struct MealCreate: Codable {
    let mealType: String
    let mealName: String?
    let dishName: String
    let calories: Int
    let protein: Double
    let fat: Double
    let carbs: Double
    let analysisType: String?
    
    enum CodingKeys: String, CodingKey {
        case mealType = "meal_type"
        case mealName = "meal_name"
        case dishName = "dish_name"
        case calories
        case protein
        case fat
        case carbs
        case analysisType = "analysis_type"
    }
}

struct MealsResponse: Codable {
    let ok: Bool
    let items: [Meal]?
    let error: String?
}

struct AddMealResponse: Codable {
    let ok: Bool
    let error: String?
}
