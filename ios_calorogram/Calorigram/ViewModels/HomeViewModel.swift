//
//  HomeViewModel.swift
//  Calorigram
//
//  ViewModel для главного экрана
//

import Foundation

@MainActor
class HomeViewModel: ObservableObject {
    @Published var todayStats: TodayStats?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let apiService = APIService.shared
    
    func loadTodayStats() async {
        isLoading = true
        errorMessage = nil
        
        do {
            todayStats = try await apiService.request(
                endpoint: Constants.API.statsToday,
                method: "GET"
            )
        } catch let error as APIError {
            errorMessage = error.localizedDescription
            print("Error loading today stats: \(error)")
        } catch {
            errorMessage = "Ошибка загрузки данных: \(error.localizedDescription)"
            print("Error loading today stats: \(error)")
        }
        
        isLoading = false
    }
}
