//
//  DiaryViewModel.swift
//  Calorigram
//
//  ViewModel для дневника
//

import Foundation

@MainActor
class DiaryViewModel: ObservableObject {
    @Published var meals: [Meal] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    var groupedMeals: [String: [Meal]] {
        Dictionary(grouping: meals, by: { $0.mealType })
    }
    
    private let apiService = APIService.shared
    
    func loadMeals() async {
        isLoading = true
        errorMessage = nil
        
        do {
            let response: MealsResponse = try await apiService.request(
                endpoint: Constants.API.mealsToday,
                method: "GET"
            )
            
            if response.ok, let items = response.items {
                meals = items
            } else {
                errorMessage = response.error ?? "Ошибка загрузки данных"
            }
        } catch let error as APIError {
            errorMessage = error.localizedDescription
            print("Error loading meals: \(error)")
        } catch {
            errorMessage = "Ошибка загрузки данных: \(error.localizedDescription)"
            print("Error loading meals: \(error)")
        }
        
        isLoading = false
    }
    
    func deleteMeal(id: Int) async {
        do {
            struct DeleteResponse: Codable {
                let ok: Bool
                let error: String?
            }
            
            let response: DeleteResponse = try await apiService.request(
                endpoint: "\(Constants.API.deleteMeal)/\(id)",
                method: "DELETE"
            )
            
            if !response.ok {
                errorMessage = response.error ?? "Ошибка удаления"
            }
        } catch {
            errorMessage = error.localizedDescription
            print("Error deleting meal: \(error)")
        }
    }
}
