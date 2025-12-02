//
//  WelcomeScreen.swift
//  Calorigram
//
//  Экран приветствия для новых пользователей
//

import SwiftUI

struct WelcomeScreen: View {
    var onContinue: () -> Void

    var body: some View {
        VStack(spacing: 30) {
            Spacer()

            // Логотип или иконка
            Image(systemName: "fork.knife.circle.fill")
                .font(.system(size: 80))
                .foregroundColor(.green)
                .padding(.bottom, 20)

            // Заголовок
            Text("Добро пожаловать в Calorigram!")
                .font(.title)
                .fontWeight(.bold)
                .multilineTextAlignment(.center)

            // Описание
            Text("Ваше приложение для отслеживания питания и достижения целей по здоровью")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)

            // Особенности
            VStack(alignment: .leading, spacing: 15) {
                FeatureRow(icon: "📊", title: "Отслеживание калорий", description: "Контролируйте свой дневной рацион")
                FeatureRow(icon: "🎯", title: "Достижение целей", description: "Похудение, набор веса или поддержание")
                FeatureRow(icon: "📱", title: "Удобный интерфейс", description: "Простое добавление приемов пищи")
                FeatureRow(icon: "📈", title: "Анализ прогресса", description: "Графики и статистика вашего пути")
            }
            .padding(.horizontal, 40)
            .padding(.top, 30)

            Spacer()

            // Кнопка продолжения
            Button(action: onContinue) {
                Text("Начать")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.green)
                    .cornerRadius(10)
                    .padding(.horizontal, 40)
            }
        }
        .padding(.vertical, 50)
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String

    var body: some View {
        HStack(alignment: .top, spacing: 15) {
            Text(icon)
                .font(.title2)

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                    .foregroundColor(.primary)

                Text(description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
        }
    }
}

struct WelcomeScreen_Previews: PreviewProvider {
    static var previews: some View {
        WelcomeScreen(onContinue: {})
    }
}