//
//  OnboardingView.swift
//  Calorigram
//
//  Onboarding экраны для новых пользователей
//

import SwiftUI

struct OnboardingView: View {
    @Binding var isPresented: Bool
    @EnvironmentObject var authViewModel: AuthViewModel
    @StateObject private var profileViewModel = ProfileViewModel()
    @State private var currentPage = 0
    @State private var name = ""
    @State private var selectedGoal: String = ""
    @State private var age: String = ""
    @State private var height: String = ""
    @State private var weight: String = ""
    @State private var gender: String = "male"
    @State private var activityLevel: String = ""
    @State private var isSaving = false
    @State private var errorMessage: String?
    
    let goals = [
        ("lose", "Похудение", "📉"),
        ("maintain", "Поддержание", "⚖️"),
        ("gain", "Набор веса", "📈")
    ]
    
    let activityLevels = [
        ("sedentary", "🛌 Малоподвижный"),
        ("light", "🏃 Легкая активность"),
        ("moderate", "💪 Умеренная активность"),
        ("active", "🔥 Высокая активность"),
        ("very_active", "⚡ Очень высокая активность")
    ]
    
    var body: some View {
        NavigationView {
            TabView(selection: $currentPage) {
                // Page 1: Welcome
                WelcomePage(onNext: {
                    withAnimation {
                        currentPage = 1
                    }
                })
                .tag(0)
                
                // Page 2: Name
                NamePage(name: $name, onNext: {
                    if !name.isEmpty {
                        withAnimation {
                            currentPage = 2
                        }
                    }
                })
                .tag(1)
                
                // Page 3: Gender
                GenderPage(gender: $gender, onNext: {
                    withAnimation {
                        currentPage = 3
                    }
                })
                .tag(2)
                
                // Page 4: Age
                AgePage(age: $age, onNext: {
                    if let ageInt = Int(age), ageInt >= 1 && ageInt <= 120 {
                        withAnimation {
                            currentPage = 4
                        }
                    }
                })
                .tag(3)
                
                // Page 5: Height
                HeightPage(height: $height, onNext: {
                    if let heightDouble = Double(height), heightDouble >= 50 && heightDouble <= 250 {
                        withAnimation {
                            currentPage = 5
                        }
                    }
                })
                .tag(4)
                
                // Page 6: Weight
                WeightPage(weight: $weight, onNext: {
                    if let weightDouble = Double(weight), weightDouble >= 20 && weightDouble <= 300 {
                        withAnimation {
                            currentPage = 6
                        }
                    }
                })
                .tag(5)
                
                // Page 7: Activity Level
                ActivityLevelPage(
                    activityLevel: $activityLevel,
                    activityLevels: activityLevels,
                    onNext: {
                        if !activityLevel.isEmpty {
                            withAnimation {
                                currentPage = 7
                            }
                        }
                    }
                )
                .tag(6)
                
                // Page 8: Goal Selection
                GoalSelectionPage(
                    selectedGoal: $selectedGoal,
                    goals: goals,
                    onComplete: {
                        saveProfile()
                    },
                    isSaving: isSaving
                )
                .tag(7)
            }
            .tabViewStyle(.page)
            .indexViewStyle(.page(backgroundDisplayMode: .always))
            .navigationBarHidden(true)
        }
        .alert("Ошибка", isPresented: .constant(errorMessage != nil)) {
            Button("OK") {
                errorMessage = nil
            }
        } message: {
            if let error = errorMessage {
                Text(error)
            }
        }
    }
    
    private func saveProfile() {
        guard let ageInt = Int(age),
              let heightDouble = Double(height),
              let weightDouble = Double(weight),
              !name.isEmpty,
              !selectedGoal.isEmpty,
              !activityLevel.isEmpty else {
            errorMessage = "Пожалуйста, заполните все поля"
            return
        }
        
        isSaving = true
        errorMessage = nil
        
        Task {
            // Сначала обновляем профиль
            let success = await profileViewModel.updateProfile(
                name: name,
                age: ageInt,
                height: heightDouble,
                weight: weightDouble,
                goal: selectedGoal,
                activityLevel: activityLevel,
                gender: gender
            )
            
            if success {
                // Затем рассчитываем калории
                await calculateProfile()
            } else {
                errorMessage = profileViewModel.errorMessage ?? "Ошибка сохранения профиля"
                isSaving = false
            }
        }
    }
    
    private func calculateProfile() async {
        guard let ageInt = Int(age),
              let heightDouble = Double(height),
              let weightDouble = Double(weight) else {
            errorMessage = "Ошибка валидации данных"
            isSaving = false
            return
        }
        
        struct CalculateRequest: Codable {
            let gender: String
            let age: Int
            let height: Double
            let weight: Double
            let activityLevel: String
            let goal: String
            
            enum CodingKeys: String, CodingKey {
                case gender
                case age
                case height
                case weight
                case activityLevel = "activity_level"
                case goal
            }
        }
        
        struct CalculateResponse: Codable {
            let success: Bool
            let message: String?
        }
        
        let request = CalculateRequest(
            gender: gender,
            age: ageInt,
            height: heightDouble,
            weight: weightDouble,
            activityLevel: activityLevel,
            goal: selectedGoal
        )
        
        do {
            let response: CalculateResponse = try await APIService.shared.request(
                endpoint: Constants.API.calculateProfile,
                method: "POST",
                body: request
            )
            
            if response.success {
                // Обновляем данные пользователя
                authViewModel.checkAuthStatus()
                
                // Закрываем onboarding
                isSaving = false
                isPresented = false
            } else {
                errorMessage = response.message ?? "Ошибка расчета профиля"
                isSaving = false
            }
        } catch {
            errorMessage = "Ошибка расчета профиля: \(error.localizedDescription)"
            isSaving = false
        }
    }
}

struct WelcomePage: View {
    let onNext: () -> Void
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            Image(systemName: "heart.text.square.fill")
                .font(.system(size: 80))
                .foregroundColor(.green)
            
            Text("Добро пожаловать в Calorigram!")
                .font(.title)
                .fontWeight(.bold)
                .multilineTextAlignment(.center)
            
            Text("Отслеживайте свое питание, анализируйте блюда и достигайте своих целей")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            Spacer()
            
            Button(action: onNext) {
                Text("Начать")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color.green)
                    )
            }
            .padding(.horizontal)
            .padding(.bottom, 40)
        }
        .padding()
    }
}

struct GoalSelectionPage: View {
    @Binding var selectedGoal: String
    let goals: [(String, String, String)]
    let onComplete: () -> Void
    let isSaving: Bool
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            Text("Выберите вашу цель")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Это поможет нам рассчитать вашу дневную норму калорий")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            VStack(spacing: 15) {
                ForEach(goals, id: \.0) { goal in
                    Button(action: {
                        selectedGoal = goal.0
                    }) {
                        HStack {
                            Text(goal.2)
                                .font(.title2)
                            Text(goal.1)
                                .font(.headline)
                            Spacer()
                            if selectedGoal == goal.0 {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                            }
                        }
                        .padding()
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(selectedGoal == goal.0 ? Color.green.opacity(0.1) : Color(.systemGray6))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(selectedGoal == goal.0 ? Color.green : Color.clear, lineWidth: 2)
                                )
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal)
            
            Spacer()
            
            Button(action: onComplete) {
                if isSaving {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .frame(maxWidth: .infinity)
                        .padding()
                } else {
                    Text("Завершить")
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                }
            }
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(selectedGoal.isEmpty ? Color.gray : Color.green)
            )
            .padding(.horizontal)
            .padding(.bottom, 40)
            .disabled(selectedGoal.isEmpty || isSaving)
        }
        .padding()
    }
}

struct NamePage: View {
    @Binding var name: String
    let onNext: () -> Void
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            Text("Как вас зовут?")
                .font(.title)
                .fontWeight(.bold)
            
            TextField("Введите ваше имя", text: $name)
                .textFieldStyle(.roundedBorder)
                .autocapitalization(.words)
                .padding(.horizontal)
            
            Spacer()
            
            Button(action: onNext) {
                Text("Далее")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(name.isEmpty ? Color.gray : Color.green)
                    )
            }
            .padding(.horizontal)
            .padding(.bottom, 40)
            .disabled(name.isEmpty)
        }
        .padding()
    }
}

struct GenderPage: View {
    @Binding var gender: String
    let onNext: () -> Void
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            Text("Выберите ваш пол")
                .font(.title)
                .fontWeight(.bold)
            
            VStack(spacing: 15) {
                Button(action: {
                    gender = "male"
                }) {
                    HStack {
                        Text("👨")
                            .font(.title2)
                        Text("Мужской")
                            .font(.headline)
                        Spacer()
                        if gender == "male" {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                        }
                    }
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(gender == "male" ? Color.green.opacity(0.1) : Color(.systemGray6))
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(gender == "male" ? Color.green : Color.clear, lineWidth: 2)
                            )
                    )
                }
                .buttonStyle(.plain)
                
                Button(action: {
                    gender = "female"
                }) {
                    HStack {
                        Text("👩")
                            .font(.title2)
                        Text("Женский")
                            .font(.headline)
                        Spacer()
                        if gender == "female" {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                        }
                    }
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(gender == "female" ? Color.green.opacity(0.1) : Color(.systemGray6))
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(gender == "female" ? Color.green : Color.clear, lineWidth: 2)
                            )
                    )
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal)
            
            Spacer()
            
            Button(action: onNext) {
                Text("Далее")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color.green)
                    )
            }
            .padding(.horizontal)
            .padding(.bottom, 40)
        }
        .padding()
    }
}

struct AgePage: View {
    @Binding var age: String
    let onNext: () -> Void
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            Text("Сколько вам лет?")
                .font(.title)
                .fontWeight(.bold)
            
            TextField("Введите возраст", text: $age)
                .textFieldStyle(.roundedBorder)
                .keyboardType(.numberPad)
                .padding(.horizontal)
            
            Spacer()
            
            Button(action: onNext) {
                Text("Далее")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(isValid ? Color.green : Color.gray)
                    )
            }
            .padding(.horizontal)
            .padding(.bottom, 40)
            .disabled(!isValid)
        }
        .padding()
    }
    
    private var isValid: Bool {
        if let ageInt = Int(age) {
            return ageInt >= 1 && ageInt <= 120
        }
        return false
    }
}

struct HeightPage: View {
    @Binding var height: String
    let onNext: () -> Void
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            Text("Какой у вас рост?")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Введите рост в сантиметрах")
                .font(.body)
                .foregroundColor(.secondary)
            
            TextField("175", text: $height)
                .textFieldStyle(.roundedBorder)
                .keyboardType(.numberPad)
                .padding(.horizontal)
            
            Spacer()
            
            Button(action: onNext) {
                Text("Далее")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(isValid ? Color.green : Color.gray)
                    )
            }
            .padding(.horizontal)
            .padding(.bottom, 40)
            .disabled(!isValid)
        }
        .padding()
    }
    
    private var isValid: Bool {
        if let heightDouble = Double(height) {
            return heightDouble >= 50 && heightDouble <= 250
        }
        return false
    }
}

struct WeightPage: View {
    @Binding var weight: String
    let onNext: () -> Void
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            Text("Какой у вас вес?")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Введите вес в килограммах")
                .font(.body)
                .foregroundColor(.secondary)
            
            TextField("70", text: $weight)
                .textFieldStyle(.roundedBorder)
                .keyboardType(.decimalPad)
                .padding(.horizontal)
            
            Spacer()
            
            Button(action: onNext) {
                Text("Далее")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(isValid ? Color.green : Color.gray)
                    )
            }
            .padding(.horizontal)
            .padding(.bottom, 40)
            .disabled(!isValid)
        }
        .padding()
    }
    
    private var isValid: Bool {
        if let weightDouble = Double(weight) {
            return weightDouble >= 20 && weightDouble <= 300
        }
        return false
    }
}

struct ActivityLevelPage: View {
    @Binding var activityLevel: String
    let activityLevels: [(String, String)]
    let onNext: () -> Void
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            Text("Выберите ваш уровень активности")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Это поможет рассчитать вашу дневную норму калорий")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            VStack(spacing: 15) {
                ForEach(activityLevels, id: \.0) { level in
                    Button(action: {
                        activityLevel = level.0
                    }) {
                        HStack {
                            Text(level.1)
                                .font(.headline)
                            Spacer()
                            if activityLevel == level.0 {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                            }
                        }
                        .padding()
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(activityLevel == level.0 ? Color.green.opacity(0.1) : Color(.systemGray6))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(activityLevel == level.0 ? Color.green : Color.clear, lineWidth: 2)
                                )
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal)
            
            Spacer()
            
            Button(action: onNext) {
                Text("Далее")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(activityLevel.isEmpty ? Color.gray : Color.green)
                    )
            }
            .padding(.horizontal)
            .padding(.bottom, 40)
            .disabled(activityLevel.isEmpty)
        }
        .padding()
    }
}

struct OnboardingView_Previews: PreviewProvider {
    static var previews: some View {
        OnboardingView(isPresented: .constant(true))
    }
}

