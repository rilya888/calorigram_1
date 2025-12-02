//
//  AddMealModal.swift
//  Calorigram
//
//  Модальное окно для добавления приема пищи
//

import SwiftUI

struct AddMealModal: View {
    @Environment(\.dismiss) var dismiss
    @StateObject private var viewModel = AddMealViewModel()
    
    @State private var selectedMealType = "breakfast"
    @State private var dishName = ""
    @State private var calories = ""
    @State private var protein = ""
    @State private var fat = ""
    @State private var carbs = ""
    
    let mealTypes = [
        ("breakfast", "Завтрак", "🌅"),
        ("lunch", "Обед", "☀️"),
        ("dinner", "Ужин", "🌙"),
        ("snack", "Перекус", "🍎")
    ]
    
    var body: some View {
        NavigationView {
            Form {
                Section("Тип приема пищи") {
                    Picker("Тип", selection: $selectedMealType) {
                        ForEach(mealTypes, id: \.0) { type, name, icon in
                            HStack {
                                Text(icon)
                                Text(name)
                            }
                            .tag(type)
                        }
                    }
                }
                
                Section("Информация о блюде") {
                    TextField("Название блюда", text: $dishName)
                    TextField("Калории", text: $calories)
                        .keyboardType(.numberPad)
                    TextField("Белки (г)", text: $protein)
                        .keyboardType(.decimalPad)
                    TextField("Жиры (г)", text: $fat)
                        .keyboardType(.decimalPad)
                    TextField("Углеводы (г)", text: $carbs)
                        .keyboardType(.decimalPad)
                }
            }
            .navigationTitle("Добавить прием пищи")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Отмена") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Добавить") {
                        Task {
                            await addMeal()
                        }
                    }
                    .disabled(!isFormValid || viewModel.isLoading)
                }
            }
            .overlay {
                if viewModel.isLoading {
                    ProgressView()
                }
            }
            .alert("Ошибка", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") {
                    viewModel.errorMessage = nil
                }
            } message: {
                if let error = viewModel.errorMessage {
                    Text(error)
                }
            }
        }
    }
    
    private var isFormValid: Bool {
        !dishName.isEmpty &&
        !calories.isEmpty &&
        Int(calories) != nil
    }
    
    private func addMeal() async {
        guard let caloriesInt = Int(calories) else { return }
        
        let proteinDouble = Double(protein) ?? 0.0
        let fatDouble = Double(fat) ?? 0.0
        let carbsDouble = Double(carbs) ?? 0.0
        
        let success = await viewModel.addMeal(
            mealType: selectedMealType,
            dishName: dishName,
            calories: caloriesInt,
            protein: proteinDouble,
            fat: fatDouble,
            carbs: carbsDouble
        )
        
        if success {
            dismiss()
        }
    }
}

struct AddMealModal_Previews: PreviewProvider {
    static var previews: some View {
        AddMealModal()
    }
}
