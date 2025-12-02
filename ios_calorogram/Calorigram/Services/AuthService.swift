//
//  AuthService.swift
//  Calorigram
//
//  Сервис для авторизации (email/password, phone, Apple)
//

import Foundation

class AuthService {
    static let shared = AuthService()
    
    private let apiService = APIService.shared
    private let keychainService = KeychainService.shared
    
    private init() {}
    
    // MARK: - Email/Password Auth
    
    func register(email: String, password: String, name: String) async throws -> AuthResponse {
        let request = RegisterRequest(email: email, password: password, name: name)
        let response: AuthResponse = try await apiService.request(
            endpoint: Constants.API.register,
            method: "POST",
            body: request,
            requiresAuth: false
        )
        
        // Сохраняем токены
        saveTokens(accessToken: response.accessToken, refreshToken: response.refreshToken)
        
        return response
    }
    
    func login(email: String, password: String) async throws -> AuthResponse {
        let request = LoginRequest(email: email, password: password)
        let response: AuthResponse = try await apiService.request(
            endpoint: Constants.API.login,
            method: "POST",
            body: request,
            requiresAuth: false
        )
        
        // Сохраняем токены
        saveTokens(accessToken: response.accessToken, refreshToken: response.refreshToken)
        
        return response
    }
    
    // MARK: - Phone Auth
    
    func sendPhoneCode(phoneNumber: String) async throws -> Bool {
        let request = PhoneSendCodeRequest(phoneNumber: phoneNumber)
        struct Response: Codable {
            let success: Bool
            let message: String?
        }
        
        let response: Response = try await apiService.request(
            endpoint: Constants.API.phoneSendCode,
            method: "POST",
            body: request,
            requiresAuth: false
        )
        
        return response.success
    }
    
    func verifyPhoneCode(phoneNumber: String, code: String) async throws -> AuthResponse {
        let request = PhoneVerifyRequest(phoneNumber: phoneNumber, code: code)
        let response: AuthResponse = try await apiService.request(
            endpoint: Constants.API.phoneVerify,
            method: "POST",
            body: request,
            requiresAuth: false
        )
        
        // Сохраняем токены
        saveTokens(accessToken: response.accessToken, refreshToken: response.refreshToken)
        
        return response
    }
    
    // MARK: - Apple Sign In
    
    func loginWithApple(identityToken: String, authorizationCode: String, userIdentifier: String, email: String?) async throws -> AuthResponse {
        let request = AppleLoginRequest(
            identityToken: identityToken,
            authorizationCode: authorizationCode,
            userIdentifier: userIdentifier,
            email: email
        )
        
        let response: AuthResponse = try await apiService.request(
            endpoint: Constants.API.appleLogin,
            method: "POST",
            body: request,
            requiresAuth: false
        )
        
        // Сохраняем токены
        saveTokens(accessToken: response.accessToken, refreshToken: response.refreshToken)
        
        return response
    }
    
    // MARK: - Token Management
    
    func isLoggedIn() -> Bool {
        return keychainService.get(forKey: Constants.Keychain.accessToken) != nil
    }
    
    func getAccessToken() -> String? {
        return keychainService.get(forKey: Constants.Keychain.accessToken)
    }
    
    func getCurrentUser() async throws -> User {
        let response: User = try await apiService.request(
            endpoint: Constants.API.profileMe,
            method: "GET"
        )
        return response
    }
    
    func logout() {
        keychainService.clearAll()
        UserDefaults.standard.removeObject(forKey: Constants.UserDefaults.isLoggedIn)
        UserDefaults.standard.removeObject(forKey: Constants.UserDefaults.userId)
    }
    
    private func saveTokens(accessToken: String, refreshToken: String) {
        _ = keychainService.save(accessToken, forKey: Constants.Keychain.accessToken)
        _ = keychainService.save(refreshToken, forKey: Constants.Keychain.refreshToken)
        UserDefaults.standard.set(true, forKey: Constants.UserDefaults.isLoggedIn)
    }
}
