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

    // Проверка валидности email
    private var isEmailValid: Bool {
        let emailRegex = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
        let emailPredicate = NSPredicate(format:"SELF MATCHES %@", emailRegex)
        return emailPredicate.evaluate(with: email)
    }

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

            // Подсказки по требованиям
            VStack(alignment: .leading, spacing: 4) {
                if !email.isEmpty && !isEmailValid {
                    Text("Введите корректный email адрес")
                        .foregroundColor(.red)
                        .font(.caption)
                }
                if !password.isEmpty && password.count < 6 {
                    Text("Пароль должен содержать минимум 6 символов")
                        .foregroundColor(.red)
                        .font(.caption)
                }
                if !isLoginMode && !name.isEmpty && name.count < 2 {
                    Text("Имя должно содержать минимум 2 символа")
                        .foregroundColor(.red)
                        .font(.caption)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 20)

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
            .disabled(authViewModel.isLoading || !isEmailValid || password.count < 6 || (!isLoginMode && name.count < 2))
            
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
