//
//  PhoneAuthView.swift
//  Calorigram
//
//  Экран авторизации по номеру телефона
//

import SwiftUI

struct PhoneAuthView: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    @State private var phoneNumber = ""
    @State private var code = ""
    @State private var codeSent = false
    @State private var showCodeInput = false
    
    var body: some View {
        VStack(spacing: 20) {
            if !showCodeInput {
                // Ввод номера телефона
                VStack(spacing: 15) {
                    Text("Введите номер телефона")
                        .font(.headline)
                    
                    TextField("+7 (999) 123-45-67", text: $phoneNumber)
                        .textFieldStyle(.roundedBorder)
                        .keyboardType(.phonePad)
                    
                    Button(action: {
                        Task {
                            let success = await authViewModel.sendPhoneCode(phoneNumber: phoneNumber)
                            if success {
                                showCodeInput = true
                            }
                        }
                    }) {
                        if authViewModel.isLoading {
                            ProgressView()
                                .frame(maxWidth: .infinity)
                                .padding()
                        } else {
                            Text("Отправить код")
                                .frame(maxWidth: .infinity)
                                .padding()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(authViewModel.isLoading || phoneNumber.isEmpty)
                }
            } else {
                // Ввод кода
                VStack(spacing: 15) {
                    Text("Введите код из SMS")
                        .font(.headline)
                    
                    Text("Код отправлен на \(phoneNumber)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    TextField("000000", text: $code)
                        .textFieldStyle(.roundedBorder)
                        .keyboardType(.numberPad)
                        .multilineTextAlignment(.center)
                        .font(.title2)
                    
                    Button(action: {
                        Task {
                            await authViewModel.verifyPhoneCode(phoneNumber: phoneNumber, code: code)
                        }
                    }) {
                        if authViewModel.isLoading {
                            ProgressView()
                                .frame(maxWidth: .infinity)
                                .padding()
                        } else {
                            Text("Подтвердить")
                                .frame(maxWidth: .infinity)
                                .padding()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(authViewModel.isLoading || code.count != 6)
                    
                    Button("Изменить номер") {
                        showCodeInput = false
                        code = ""
                    }
                    .foregroundColor(.blue)
                }
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

struct PhoneAuthView_Previews: PreviewProvider {
    static var previews: some View {
        PhoneAuthView()
            .environmentObject(AuthViewModel())
    }
}
