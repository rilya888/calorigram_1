//
//  AddMealViewModel.swift
//  Calorigram
//
//  ViewModel для добавления приема пищи
//

import Foundation

@MainActor
class AddMealViewModel: ObservableObject {
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let apiService = APIService.shared
    
    func addMeal(
        mealType: String,
        dishName: String,
        calories: Int,
        protein: Double,
        fat: Double,
        carbs: Double
    ) async -> Bool {
        isLoading = true
        errorMessage = nil
        
        let meal = MealCreate(
            mealType: mealType,
            mealName: nil,
            dishName: dishName,
            calories: calories,
            protein: protein,
            fat: fat,
            carbs: carbs,
            analysisType: "manual"
        )
        
        do {
            let response: AddMealResponse = try await apiService.request(
                endpoint: Constants.API.addMeal,
                method: "POST",
                body: meal
            )
            
            isLoading = false
            return response.ok
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
            return false
        }
    }
}
