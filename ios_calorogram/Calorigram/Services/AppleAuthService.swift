//
//  AppleAuthService.swift
//  Calorigram
//
//  Сервис для Apple Sign In
//

import Foundation
import AuthenticationServices
import UIKit

class AppleAuthService: NSObject, ASAuthorizationControllerDelegate, ASAuthorizationControllerPresentationContextProviding {
    
    static let shared = AppleAuthService()
    
    private var completionHandler: ((Result<AuthResponse, Error>) -> Void)?
    private let authService = AuthService.shared
    
    private override init() {
        super.init()
    }
    
    func signIn() async throws -> AuthResponse {
        // Этот метод больше не используется напрямую
        // Apple Sign In обрабатывается через SignInWithAppleButton в SwiftUI
        throw NSError(domain: "AppleAuth", code: -1, userInfo: [NSLocalizedDescriptionKey: "Use SignInWithAppleButton instead"])
    }
    
    func handleAppleSignInResult(identityToken: String, authorizationCode: String, userIdentifier: String, email: String?) async throws -> AuthResponse {
        return try await authService.loginWithApple(
            identityToken: identityToken,
            authorizationCode: authorizationCode,
            userIdentifier: userIdentifier,
            email: email
        )
    }
    
    // MARK: - ASAuthorizationControllerDelegate
    
    func authorizationController(controller: ASAuthorizationController, didCompleteWithAuthorization authorization: ASAuthorization) {
        if let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential {
            guard let identityTokenData = appleIDCredential.identityToken,
                  let identityToken = String(data: identityTokenData, encoding: .utf8),
                  let authorizationCodeData = appleIDCredential.authorizationCode,
                  let authorizationCode = String(data: authorizationCodeData, encoding: .utf8) else {
                completionHandler?(.failure(NSError(domain: "AppleAuth", code: -1, userInfo: [NSLocalizedDescriptionKey: "Failed to get tokens"])))
                return
            }
            
            let userIdentifier = appleIDCredential.user
            let email = appleIDCredential.email
            
            Task {
                do {
                    let response = try await authService.loginWithApple(
                        identityToken: identityToken,
                        authorizationCode: authorizationCode,
                        userIdentifier: userIdentifier,
                        email: email
                    )
                    completionHandler?(.success(response))
                } catch {
                    completionHandler?(.failure(error))
                }
            }
        }
    }
    
    func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        completionHandler?(.failure(error))
    }
    
    // MARK: - ASAuthorizationControllerPresentationContextProviding
    
    func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
        // Возвращаем главное окно приложения
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let window = windowScene.windows.first {
            return window
        }
        // Fallback
        return UIWindow()
    }
}
