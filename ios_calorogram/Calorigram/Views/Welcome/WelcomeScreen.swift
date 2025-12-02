//
//  WelcomeScreen.swift
//  Calorigram
//
//  Приветственный экран после регистрации
//

import SwiftUI

struct WelcomeScreen: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    let onContinue: () -> Void
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            // Иконка/Логотип
            Image(systemName: "heart.text.square.fill")
                .font(.system(size: 100))
                .foregroundColor(.green)
                .padding(.bottom, 20)
            
            // Приветствие
            VStack(spacing: 15) {
                Text("Привет, \(authViewModel.currentUser?.name ?? "Пользователь")! 👋")
                    .font(.title)
                    .fontWeight(.bold)
                    .multilineTextAlignment(.center)
                
                Text("Добро пожаловать в Calorigram!")
                    .font(.title2)
                    .fontWeight(.semibold)
                    .multilineTextAlignment(.center)
            }
            .padding(.bottom, 30)
            
            // Описание возможностей
            VStack(alignment: .leading, spacing: 20) {
                FeatureRow(icon: "chart.bar.fill", title: "Расчет калорий", description: "Рассчитаем вашу суточную норму")
                FeatureRow(icon: "flame.fill", title: "Отслеживание прогресса", description: "Следите за своими достижениями")
                FeatureRow(icon: "leaf.fill", title: "Рекомендации", description: "Персональные советы по питанию")
            }
            .padding(.horizontal, 40)
            
            Spacer()
            
            // Кнопка продолжения
            Button(action: {
                onContinue()
            }) {
                Text("Начать")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        LinearGradient(
                            gradient: Gradient(colors: [.green, .blue]),
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .cornerRadius(12)
            }
            .padding(.horizontal, 40)
            .padding(.bottom, 40)
        }
        .background(
            LinearGradient(
                gradient: Gradient(colors: [Color(.systemBackground), Color.green.opacity(0.1)]),
                startPoint: .top,
                endPoint: .bottom
            )
        )
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String
    
    var body: some View {
        HStack(spacing: 15) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.green)
                .frame(width: 40)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                
                Text(description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
    }
}

struct WelcomeScreen_Previews: PreviewProvider {
    static var previews: some View {
        WelcomeScreen(onContinue: {})
            .environmentObject(AuthViewModel())
    }
}

