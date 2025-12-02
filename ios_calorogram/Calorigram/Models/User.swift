//
//  User.swift
//  Calorigram
//
//  Модель пользователя
//

import Foundation

struct User: Codable, Identifiable {
    let id: Int
    let email: String?
    let phoneNumber: String?
    let name: String
    let gender: String?
    let age: Int?
    let height: Double?
    let weight: Double?
    let activityLevel: String?
    let goal: String?
    let targetCalories: Int?
    let targetProtein: Double?
    let targetFat: Double?
    let targetCarbs: Double?
    let subscriptionType: String?
    let subscriptionExpiresAt: String?
    let isPremium: Bool?
    let createdAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case email
        case phoneNumber = "phone_number"
        case name
        case gender
        case age
        case height
        case weight
        case activityLevel = "activity_level"
        case goal
        case targetCalories = "target_calories"
        case targetProtein = "target_protein"
        case targetFat = "target_fat"
        case targetCarbs = "target_carbs"
        case subscriptionType = "subscription_type"
        case subscriptionExpiresAt = "subscription_expires_at"
        case isPremium = "is_premium"
        case createdAt = "created_at"
    }
}

struct AuthResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
    let user: User
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case tokenType = "token_type"
        case user
    }
}

struct RegisterRequest: Codable {
    let email: String
    let password: String
    let name: String
}

struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct PhoneSendCodeRequest: Codable {
    let phoneNumber: String
    
    enum CodingKeys: String, CodingKey {
        case phoneNumber = "phone_number"
    }
}

struct PhoneVerifyRequest: Codable {
    let phoneNumber: String
    let code: String
    
    enum CodingKeys: String, CodingKey {
        case phoneNumber = "phone_number"
        case code
    }
}

struct AppleLoginRequest: Codable {
    let identityToken: String
    let authorizationCode: String
    let userIdentifier: String
    let email: String?
    
    enum CodingKeys: String, CodingKey {
        case identityToken = "identity_token"
        case authorizationCode = "authorization_code"
        case userIdentifier = "user_identifier"
        case email
    }
}

struct RefreshTokenRequest: Codable {
    let refreshToken: String
    
    enum CodingKeys: String, CodingKey {
        case refreshToken = "refresh_token"
    }
}

struct RefreshTokenResponse: Codable {
    let accessToken: String
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
    }
}
