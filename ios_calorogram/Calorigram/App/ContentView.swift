//
//  ContentView.swift
//  Calorigram
//
//  Корневой view приложения
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false
    @AppStorage("hasSeenWelcome") private var hasSeenWelcome = false
    @State private var showOnboarding = false
    @State private var showWelcome = false
    
    // Проверяем, зарегистрирован ли пользователь (есть ли базовые данные профиля)
    private var isUserRegistered: Bool {
        guard let user = authViewModel.currentUser else { return false }
        // Проверяем, есть ли хотя бы одно поле профиля заполнено
        // Если все поля nil - пользователь только что зарегистрировался
        return user.age != nil && user.height != nil && user.weight != nil
    }
    
    var body: some View {
        Group {
            if authViewModel.isAuthenticated {
                let _ = print("📱 ContentView: User is authenticated, currentUser: \(authViewModel.currentUser?.name ?? "nil")")
                let _ = print("📱 isUserRegistered: \(isUserRegistered)")
                let _ = print("📱 hasSeenWelcome: \(hasSeenWelcome)")
                let _ = print("📱 hasCompletedOnboarding: \(hasCompletedOnboarding)")
                
                // Если данные пользователя еще не загружены, показываем загрузку
                if authViewModel.currentUser == nil {
                    VStack {
                        ProgressView()
                            .scaleEffect(1.5)
                        Text("Загрузка...")
                            .foregroundColor(.secondary)
                            .padding(.top, 20)
                    }
                } else if !hasSeenWelcome && !isUserRegistered {
                    // Шаг 1: Приветственный экран (показывается один раз после регистрации)
                    WelcomeScreen {
                        withAnimation {
                            hasSeenWelcome = true
                            showOnboarding = true
                        }
                    }
                } else if (!hasCompletedOnboarding && !isUserRegistered) || showOnboarding {
                    // Шаг 2: Onboarding (заполнение профиля)
                    OnboardingView(isPresented: $showOnboarding)
                        .onAppear {
                            showOnboarding = true
                        }
                        .onChange(of: showOnboarding) { newValue in
                            if !newValue {
                                hasCompletedOnboarding = true
                            }
                        }
                        .onChange(of: authViewModel.currentUser?.age) { _ in
                            checkOnboardingComplete()
                        }
                        .onChange(of: authViewModel.currentUser?.height) { _ in
                            checkOnboardingComplete()
                        }
                        .onChange(of: authViewModel.currentUser?.weight) { _ in
                            checkOnboardingComplete()
                        }
                } else {
                    // Шаг 3: Главное приложение
                    MainTabView()
                }
            } else {
                // Не авторизован - показываем экран авторизации
                AuthView()
            }
        }
        .onAppear {
            authViewModel.checkAuthStatus()
            // При старте приложения проверяем, нужно ли сбросить флаги onboarding
            resetOnboardingFlagsIfNeeded()
        }
        .onChange(of: authViewModel.currentUser?.age) { _ in
            // При загрузке данных пользователя проверяем, нужно ли сбросить флаги
            resetOnboardingFlagsIfNeeded()
        }
        .onChange(of: authViewModel.currentUser?.height) { _ in
            resetOnboardingFlagsIfNeeded()
        }
        .onChange(of: authViewModel.currentUser?.weight) { _ in
            resetOnboardingFlagsIfNeeded()
        }
    }
    
    private func checkOnboardingComplete() {
        if let user = authViewModel.currentUser,
           user.age != nil,
           user.height != nil,
           user.weight != nil {
            // Профиль заполнен - отмечаем onboarding как завершенный
            hasCompletedOnboarding = true
            hasSeenWelcome = true
            showOnboarding = false
        }
    }
    
    private func resetOnboardingFlagsIfNeeded() {
        // Если пользователь уже зарегистрирован (профиль заполнен), сбрасываем флаги
        if isUserRegistered {
            hasCompletedOnboarding = true
            hasSeenWelcome = true
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .environmentObject(AuthViewModel())
    }
}
