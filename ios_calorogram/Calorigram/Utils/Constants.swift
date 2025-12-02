//
//  Constants.swift
//  Calorigram
//
//  Created on iOS App
//

import Foundation

struct Constants {
    // Backend API URL
    static let apiBaseURL = "https://calorigramback-production.up.railway.app/api"
    
    // API Endpoints
    struct API {
        // Auth
        static let register = "/auth/register"
        static let login = "/auth/login"
        static let phoneSendCode = "/auth/phone/send-code"
        static let phoneVerify = "/auth/phone/verify"
        static let appleLogin = "/auth/apple/login"
        static let refreshToken = "/auth/refresh"
        
        // Meals
        static let mealsToday = "/meals/today"
        static let addMeal = "/meals"
        static let deleteMeal = "/meals" // Используется как /meals/{id}
        
        // Statistics
        static let statsToday = "/statistics/today"
        static let statsWeek = "/statistics/week"
        static let statsYesterday = "/statistics/yesterday"
        
        // Profile
        static let profileMe = "/profile/me"
        static let updateProfile = "/profile"
        static let calculateProfile = "/profile/calculate"
        
        // Subscription
        static let subscriptionStatus = "/subscription/status"
    }
    
    // Keychain Keys
    struct Keychain {
        static let accessToken = "com.calorigram.accessToken"
        static let refreshToken = "com.calorigram.refreshToken"
    }
    
    // UserDefaults Keys
    struct UserDefaults {
        static let isLoggedIn = "com.calorigram.isLoggedIn"
        static let userId = "com.calorigram.userId"
    }
}
