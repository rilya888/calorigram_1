//
//  AppleAuthView.swift
//  Calorigram
//
//  Экран авторизации через Apple Sign In
//

import SwiftUI
import AuthenticationServices

struct AppleAuthView: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Войдите с помощью Apple ID")
                .font(.headline)
                .multilineTextAlignment(.center)
            
            SignInWithAppleButton(
                onRequest: { request in
                    request.requestedScopes = [.fullName, .email]
                },
                onCompletion: { result in
                    switch result {
                    case .success(let authorization):
                        if let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential {
                            guard let identityTokenData = appleIDCredential.identityToken,
                                  let identityToken = String(data: identityTokenData, encoding: .utf8),
                                  let authorizationCodeData = appleIDCredential.authorizationCode,
                                  let authorizationCode = String(data: authorizationCodeData, encoding: .utf8) else {
                                authViewModel.errorMessage = "Не удалось получить токены"
                                return
                            }
                            
                            let userIdentifier = appleIDCredential.user
                            let email = appleIDCredential.email
                            
                            Task {
                                await authViewModel.handleAppleSignIn(
                                    identityToken: identityToken,
                                    authorizationCode: authorizationCode,
                                    userIdentifier: userIdentifier,
                                    email: email
                                )
                            }
                        }
                    case .failure(let error):
                        authViewModel.errorMessage = error.localizedDescription
                    }
                }
            )
            .signInWithAppleButtonStyle(.black)
            .frame(height: 50)
            .cornerRadius(8)
            
            if authViewModel.isLoading {
                ProgressView()
            }
            
            // Ошибка
            if let errorMessage = authViewModel.errorMessage {
                Text(errorMessage)
                    .foregroundColor(.red)
                    .font(.caption)
                    .multilineTextAlignment(.center)
            }
        }
    }
}

struct AppleAuthView_Previews: PreviewProvider {
    static var previews: some View {
        AppleAuthView()
            .environmentObject(AuthViewModel())
    }
}
