//
//  Subscription.swift
//  Calorigram
//
//  Модель подписки
//

import Foundation

struct Subscription: Codable {
    let isActive: Bool
    let type: String
    let expiresAt: String?
    let daysRemaining: Int
    let features: SubscriptionFeatures
    
    enum CodingKeys: String, CodingKey {
        case isActive = "is_active"
        case type
        case expiresAt = "expires_at"
        case daysRemaining = "days_remaining"
        case features
    }
}

struct SubscriptionFeatures: Codable {
    let mealAnalysis: Bool
    let unlimitedMeals: Bool
    let advancedStats: Bool
    let exportData: Bool
    
    enum CodingKeys: String, CodingKey {
        case mealAnalysis = "meal_analysis"
        case unlimitedMeals = "unlimited_meals"
        case advancedStats = "advanced_stats"
        case exportData = "export_data"
    }
}
