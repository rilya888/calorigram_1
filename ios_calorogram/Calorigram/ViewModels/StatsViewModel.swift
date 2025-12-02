//
//  StatsViewModel.swift
//  Calorigram
//
//  ViewModel для статистики
//

import Foundation

@MainActor
class StatsViewModel: ObservableObject {
    @Published var weekStats: WeekStats?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let apiService = APIService.shared
    
    func loadStats() async {
        isLoading = true
        errorMessage = nil
        
        do {
            weekStats = try await apiService.request(
                endpoint: Constants.API.statsWeek,
                method: "GET"
            )
        } catch let error as APIError {
            errorMessage = error.localizedDescription
            print("Error loading stats: \(error)")
        } catch {
            errorMessage = "Ошибка загрузки данных: \(error.localizedDescription)"
            print("Error loading stats: \(error)")
        }
        
        isLoading = false
    }
}
