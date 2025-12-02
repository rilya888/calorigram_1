//
//  EmailAuthView.swift
//  Calorigram
//
//  Экран авторизации через email/password
//

import SwiftUI

struct EmailAuthView: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    @Binding var isLoginMode: Bool
    @State private var email = ""
    @State private var password = ""
    @State private var name = ""
    
    var body: some View {
        VStack(spacing: 20) {
            // Поля ввода
            VStack(spacing: 15) {
                if !isLoginMode {
                    TextField("Имя", text: $name)
                        .textFieldStyle(.roundedBorder)
                        .autocapitalization(.words)
                }
                
                TextField("Email", text: $email)
                    .textFieldStyle(.roundedBorder)
                    .keyboardType(.emailAddress)
                    .autocapitalization(.none)
                
                SecureField("Пароль", text: $password)
                    .textFieldStyle(.roundedBorder)
            }
            
            // Кнопка действия
            Button(action: {
                Task {
                    if isLoginMode {
                        await authViewModel.login(email: email, password: password)
                    } else {
                        await authViewModel.register(email: email, password: password, name: name)
                    }
                }
            }) {
                if authViewModel.isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                        .padding()
                } else {
                    Text(isLoginMode ? "Войти" : "Зарегистрироваться")
                        .frame(maxWidth: .infinity)
                        .padding()
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(authViewModel.isLoading || email.isEmpty || password.isEmpty || (!isLoginMode && name.isEmpty))
            
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

struct EmailAuthView_Previews: PreviewProvider {
    static var previews: some View {
        EmailAuthView(isLoginMode: .constant(true))
            .environmentObject(AuthViewModel())
    }
}
