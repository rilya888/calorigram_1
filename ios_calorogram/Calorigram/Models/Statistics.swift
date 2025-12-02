//
//  Statistics.swift
//  Calorigram
//
//  Модель статистики
//

import Foundation

struct TodayStats: Codable {
    let macros: Macros
    let caloriesConsumed: Int
    let caloriesGoal: Int
    let proteinGoal: Double
    let fatGoal: Double
    let carbsGoal: Double
    
    enum CodingKeys: String, CodingKey {
        case macros
        case caloriesConsumed = "calories_consumed"
        case caloriesGoal = "calories_goal"
        case proteinGoal = "protein_goal"
        case fatGoal = "fat_goal"
        case carbsGoal = "carbs_goal"
    }
}

struct Macros: Codable {
    let protein: Double
    let fat: Double
    let carbs: Double
}

struct WeekStats: Codable {
    let targetCalories: Int
    let days: [DayStats]
    
    enum CodingKeys: String, CodingKey {
        case targetCalories = "target_calories"
        case days
    }
}

struct DayStats: Codable, Identifiable {
    let id = UUID()
    let day: String
    let date: String
    let calories: Int
    let percentage: Double
    let color: String
    
    enum CodingKeys: String, CodingKey {
        case day
        case date
        case calories
        case percentage
        case color
    }
}
