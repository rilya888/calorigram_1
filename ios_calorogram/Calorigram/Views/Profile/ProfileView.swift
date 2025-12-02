//
//  ProfileView.swift
//  Calorigram
//
//  Экран профиля
//

import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    @State private var showEditProfile = false
    @State private var showRemindersSettings = false
    
    var body: some View {
        NavigationView {
            List {
                Section {
                    if let user = authViewModel.currentUser {
                        HStack {
                            Text("Имя:")
                            Spacer()
                            Text(user.name)
                                .foregroundColor(.secondary)
                        }
                        
                        if let email = user.email {
                            HStack {
                                Text("Email:")
                                Spacer()
                                Text(email)
                                    .foregroundColor(.secondary)
                            }
                        }
                        
                        if let phone = user.phoneNumber {
                            HStack {
                                Text("Телефон:")
                                Spacer()
                                Text(phone)
                                    .foregroundColor(.secondary)
                            }
                        }
                        
                        if let age = user.age {
                            HStack {
                                Text("Возраст:")
                                Spacer()
                                Text("\(age) лет")
                                    .foregroundColor(.secondary)
                            }
                        }
                        
                        if let height = user.height {
                            HStack {
                                Text("Рост:")
                                Spacer()
                                Text("\(Int(height)) см")
                                    .foregroundColor(.secondary)
                            }
                        }
                        
                        if let weight = user.weight {
                            HStack {
                                Text("Вес:")
                                Spacer()
                                Text("\(Int(weight)) кг")
                                    .foregroundColor(.secondary)
                            }
                        }
                        
                        if let goal = user.goal {
                            HStack {
                                Text("Цель:")
                                Spacer()
                                Text(goalName(goal))
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
                
                Section {
                    Button(action: {
                        showEditProfile = true
                    }) {
                        HStack {
                            Image(systemName: "pencil")
                            Text("Редактировать профиль")
                        }
                    }
                    
                    Button(action: {
                        showRemindersSettings = true
                    }) {
                        HStack {
                            Image(systemName: "bell")
                            Text("Напоминания")
                        }
                    }
                }
                
                Section {
                    Button(action: {
                        authViewModel.logout()
                    }) {
                        HStack {
                            Image(systemName: "arrow.right.square")
                            Text("Выйти")
                        }
                        .foregroundColor(.red)
                    }
                }
                
                // DEBUG: Временная кнопка для очистки всех данных
                Section(header: Text("Отладка")) {
                    Button(action: {
                        // Logout
                        authViewModel.logout()
                        
                        // Очистить AppStorage флаги
                        UserDefaults.standard.removeObject(forKey: "hasCompletedOnboarding")
                        UserDefaults.standard.removeObject(forKey: "hasSeenWelcome")
                        
                        print("✅ All data cleared!")
                    }) {
                        HStack {
                            Image(systemName: "trash")
                            Text("Очистить все данные")
                        }
                        .foregroundColor(.orange)
                    }
                    
                    if let user = authViewModel.currentUser {
                        Text("User ID: \(user.id)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("Профиль")
            .sheet(isPresented: $showEditProfile) {
                EditProfileView()
                    .environmentObject(authViewModel)
            }
            .sheet(isPresented: $showRemindersSettings) {
                RemindersSettingsModal()
            }
        }
    }
    
    private func goalName(_ goal: String) -> String {
        switch goal {
        case "lose": return "Похудение"
        case "maintain": return "Поддержание"
        case "gain": return "Набор веса"
        default: return goal.capitalized
        }
    }
}

struct ProfileView_Previews: PreviewProvider {
    static var previews: some View {
        ProfileView()
            .environmentObject(AuthViewModel())
    }
}
