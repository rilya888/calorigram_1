//
//  AuthView.swift
//  Calorigram
//
//  Главный экран авторизации с выбором метода
//

import SwiftUI

enum RegistrationMethod: String, CaseIterable {
    case email = "Email"
    case phone = "Телефон"
    case apple = "Apple ID"
    
    var icon: String {
        switch self {
        case .email: return "envelope.fill"
        case .phone: return "phone.fill"
        case .apple: return "applelogo"
        }
    }
    
    var description: String {
        switch self {
        case .email: return "Регистрация через email"
        case .phone: return "Регистрация через телефон"
        case .apple: return "Войти через Apple"
        }
    }
}

struct RegistrationMethodView: View {
    @Binding var selectedMethod: RegistrationMethod
    let onMethodSelected: (RegistrationMethod) -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Выберите способ регистрации")
                .font(.title2)
                .fontWeight(.semibold)
                .padding(.top, 40)
            
            Text("Выберите удобный для вас способ")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .padding(.bottom, 30)
            
            VStack(spacing: 15) {
                ForEach(RegistrationMethod.allCases, id: \.self) { method in
                    Button(action: {
                        selectedMethod = method
                        onMethodSelected(method)
                    }) {
                        HStack {
                            Image(systemName: method.icon)
                                .font(.title2)
                                .foregroundColor(.blue)
                                .frame(width: 40)
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text(method.rawValue)
                                    .font(.headline)
                                    .foregroundColor(.primary)
                                
                                Text(method.description)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
                            
                            Image(systemName: "chevron.right")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding()
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(selectedMethod == method ? Color.blue.opacity(0.1) : Color(.systemGray6))
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(selectedMethod == method ? Color.blue : Color.clear, lineWidth: 2)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal)
            
            Spacer()
        }
    }
}

struct AuthView: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    @State private var showRegistrationMethod = true
    @State private var selectedMethod: RegistrationMethod = .email
    @State private var isLoginMode = true
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Логотип/Заголовок
                VStack(spacing: 10) {
                    Text("Calorigram")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Text("Следите за калориями")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.top, 60)
                .padding(.bottom, 40)
                
                if showRegistrationMethod {
                    // Экран выбора способа регистрации
                    RegistrationMethodView(selectedMethod: $selectedMethod) { method in
                        withAnimation {
                            showRegistrationMethod = false
                        }
                    }
                } else {
                    // Форма авторизации/регистрации
                    VStack(spacing: 20) {
                        // Переключатель Login/Register
                        Picker("Режим", selection: $isLoginMode) {
                            Text("Вход").tag(true)
                            Text("Регистрация").tag(false)
                        }
                        .pickerStyle(.segmented)
                        .padding(.horizontal)
                        
                        // Форма ввода
                        Group {
                            switch selectedMethod {
                            case .email:
                                EmailAuthView(isLoginMode: $isLoginMode)
                            case .phone:
                                PhoneAuthView()
                            case .apple:
                                AppleAuthView()
                            }
                        }
                        .padding(.horizontal)
                        
                        // Кнопка "Назад"
                        Button(action: {
                            withAnimation {
                                showRegistrationMethod = true
                            }
                        }) {
                            Text("Назад")
                                .foregroundColor(.blue)
                        }
                        .padding(.top, 20)
                    }
                }
                
                Spacer()
            }
            .navigationBarHidden(true)
        }
    }
}

struct AuthView_Previews: PreviewProvider {
    static var previews: some View {
        AuthView()
            .environmentObject(AuthViewModel())
    }
}
