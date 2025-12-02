//
//  AuthViewModel.swift
//  Calorigram
//
//  ViewModel для управления состоянием авторизации
//

import Foundation
import SwiftUI

@MainActor
class AuthViewModel: ObservableObject {
    @Published var isAuthenticated = false
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var currentUser: User?
    
    private let authService = AuthService.shared
    
    init() {
        checkAuthStatus()
    }
    
    func checkAuthStatus() {
        let hasToken = authService.isLoggedIn()
        
        print("🔍 checkAuthStatus() called")
        print("🔍 hasToken: \(hasToken)")
        
        if hasToken {
            print("⚠️ Found token in Keychain, verifying...")
            // Есть токен - проверяем его валидность, загружая данные пользователя
            Task {
                await loadCurrentUser()
            }
        } else {
            print("✅ No token found, user is not authenticated")
            // Нет токена - пользователь не авторизован
            isAuthenticated = false
            currentUser = nil
        }
    }
    
    private func loadCurrentUser() async {
        do {
            print("🔍 Loading current user...")
            let user = try await authService.getCurrentUser()
            print("✅ User loaded: \(user.name), id: \(user.id)")
            await MainActor.run {
                currentUser = user
                isAuthenticated = true
            }
        } catch let apiError as APIError {
            print("⚠️ Failed to load current user: \(apiError)")

            // Специальная обработка для разных типов ошибок
            var shouldLogout = false

            switch apiError {
            case .invalidURL:
                print("🔗 Invalid URL")
                shouldLogout = true

            case .noData:
                print("📄 No data received")
                shouldLogout = true

            case .unauthorized:
                print("🚪 Token expired or invalid")
                shouldLogout = true

            case .serverError(let code, let message):
                if code == 404 && message.contains("not found") {
                    print("👤 User not found (possibly deleted from admin panel)")
                    shouldLogout = true
                } else {
                    print("🚨 Server error \(code): \(message)")
                    shouldLogout = true
                }

            case .decodingError:
                print("📄 Failed to decode response")
                shouldLogout = true

            case .networkError:
                print("🌐 Network error - keeping tokens for retry")
                shouldLogout = false

            case .timeout:
                print("⏱️ Request timeout - keeping tokens for retry")
                shouldLogout = false

            case .unknown:
                print("❓ Unknown error")
                shouldLogout = true
            }

            if shouldLogout {
                await MainActor.run {
                    isAuthenticated = false
                    currentUser = nil
                    // Очищаем токены, так как они невалидны или пользователь удален
                    authService.logout()
                }
            }
        } catch {
            print("⚠️ Unexpected error loading current user: \(error)")
            await MainActor.run {
                isAuthenticated = false
                currentUser = nil
                authService.logout()
            }
        }
    }
    
    // MARK: - Email/Password Auth
    
    func register(email: String, password: String, name: String) async {
        isLoading = true
        errorMessage = nil
        
        do {
            print("📝 Starting registration for email: \(email)")
            let response = try await authService.register(email: email, password: password, name: name)
            print("✅ Registration successful, user ID: \(response.user.id)")
            currentUser = response.user
            isAuthenticated = true
            
            // Загружаем полные данные пользователя после регистрации
            await loadCurrentUser()
        } catch {
            print("❌ Registration error: \(error)")
            if let apiError = error as? APIError {
                // Улучшаем сообщение об ошибке для пользователя
                if case .serverError(let code, let message) = apiError {
                    if code == 400 {
                        // Извлекаем понятное сообщение из ответа сервера
                        if message.contains("Invalid input data") {
                            if message.contains("email") && message.contains("not a valid email") {
                                errorMessage = "Введите корректный email адрес"
                            } else if message.contains("required") {
                                errorMessage = "Заполните все обязательные поля"
                            } else {
                                errorMessage = "Неверные данные. Проверьте введенную информацию."
                            }
                        } else if message.contains("already registered") || message.contains("уже зарегистрирован") {
                            errorMessage = "Этот email уже зарегистрирован. Попробуйте войти."
                        } else {
                            errorMessage = message
                        }
                    } else {
                        errorMessage = apiError.errorDescription
                    }
                } else {
                    errorMessage = apiError.errorDescription
                }
            } else {
                errorMessage = "Ошибка регистрации: \(error.localizedDescription)"
            }
        }
        
        isLoading = false
    }
    
    func login(email: String, password: String) async {
        isLoading = true
        errorMessage = nil
        
        do {
            print("🔐 Starting login for email: \(email)")
            let response = try await authService.login(email: email, password: password)
            print("✅ Login successful, user ID: \(response.user.id)")
            currentUser = response.user
            isAuthenticated = true
            
            // Загружаем полные данные пользователя после входа
            await loadCurrentUser()
        } catch {
            print("❌ Login error: \(error)")
            if let apiError = error as? APIError {
                errorMessage = apiError.errorDescription
            } else {
                errorMessage = "Ошибка входа: \(error.localizedDescription)"
            }
        }
        
        isLoading = false
    }
    
    // MARK: - Phone Auth
    
    func sendPhoneCode(phoneNumber: String) async -> Bool {
        isLoading = true
        errorMessage = nil
        
        do {
            let success = try await authService.sendPhoneCode(phoneNumber: phoneNumber)
            isLoading = false
            return success
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
            return false
        }
    }
    
    func verifyPhoneCode(phoneNumber: String, code: String) async {
        isLoading = true
        errorMessage = nil
        
        do {
            let response = try await authService.verifyPhoneCode(phoneNumber: phoneNumber, code: code)
            currentUser = response.user
            isAuthenticated = true
            
            // Загружаем полные данные пользователя после авторизации
            await loadCurrentUser()
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    // MARK: - Apple Sign In
    
    func handleAppleSignIn(identityToken: String, authorizationCode: String, userIdentifier: String, email: String?) async {
        isLoading = true
        errorMessage = nil
        
        do {
            let response = try await AppleAuthService.shared.handleAppleSignInResult(
                identityToken: identityToken,
                authorizationCode: authorizationCode,
                userIdentifier: userIdentifier,
                email: email
            )
            currentUser = response.user
            isAuthenticated = true
            
            // Загружаем полные данные пользователя после авторизации
            await loadCurrentUser()
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    // MARK: - Logout
    
    func logout() {
        authService.logout()
        isAuthenticated = false
        currentUser = nil
    }
}
