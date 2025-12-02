//
//  EditProfileView.swift
//  Calorigram
//
//  Экран редактирования профиля
//

import SwiftUI

struct EditProfileView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var authViewModel: AuthViewModel
    @StateObject private var viewModel = ProfileViewModel()
    
    @State private var name: String = ""
    @State private var age: String = ""
    @State private var height: String = ""
    @State private var weight: String = ""
    @State private var selectedGoal = "maintain"
    @State private var selectedActivity = "moderate"
    
    let goals = [
        ("lose", "Похудение"),
        ("maintain", "Поддержание"),
        ("gain", "Набор веса")
    ]
    
    let activities = [
        ("sedentary", "Малоподвижный"),
        ("light", "Легкая активность"),
        ("moderate", "Умеренная активность"),
        ("active", "Высокая активность"),
        ("very_active", "Очень высокая активность")
    ]
    
    var body: some View {
        NavigationView {
            Form {
                Section("Основная информация") {
                    TextField("Имя", text: $name)
                    TextField("Возраст", text: $age)
                        .keyboardType(.numberPad)
                    TextField("Рост (см)", text: $height)
                        .keyboardType(.decimalPad)
                    TextField("Вес (кг)", text: $weight)
                        .keyboardType(.decimalPad)
                }
                
                Section("Цель") {
                    Picker("Цель", selection: $selectedGoal) {
                        ForEach(goals, id: \.0) { value, label in
                            Text(label).tag(value)
                        }
                    }
                }
                
                Section("Активность") {
                    Picker("Уровень активности", selection: $selectedActivity) {
                        ForEach(activities, id: \.0) { value, label in
                            Text(label).tag(value)
                        }
                    }
                }
            }
            .navigationTitle("Редактировать профиль")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Отмена") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Сохранить") {
                        Task {
                            await saveProfile()
                        }
                    }
                    .disabled(viewModel.isLoading)
                }
            }
            .task {
                loadProfile()
            }
        }
    }
    
    private func loadProfile() {
        if let user = authViewModel.currentUser {
            name = user.name
            if let ageValue = user.age {
                age = String(ageValue)
            }
            if let heightValue = user.height {
                height = String(Int(heightValue))
            }
            if let weightValue = user.weight {
                weight = String(Int(weightValue))
            }
            selectedGoal = user.goal ?? "maintain"
            selectedActivity = user.activityLevel ?? "moderate"
        }
    }
    
    private func saveProfile() async {
        let success = await viewModel.updateProfile(
            name: name,
            age: Int(age),
            height: Double(height),
            weight: Double(weight),
            goal: selectedGoal,
            activityLevel: selectedActivity
        )
        
        if success {
            dismiss()
            // Обновляем данные пользователя
            authViewModel.checkAuthStatus()
        }
    }
}

struct EditProfileView_Previews: PreviewProvider {
    static var previews: some View {
        EditProfileView()
            .environmentObject(AuthViewModel())
    }
}
