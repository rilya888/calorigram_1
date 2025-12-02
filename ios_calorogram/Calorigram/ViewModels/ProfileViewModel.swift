//
//  ProfileViewModel.swift
//  Calorigram
//
//  ViewModel для профиля
//

import Foundation

@MainActor
class ProfileViewModel: ObservableObject {
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let apiService = APIService.shared
    
    func updateProfile(
        name: String,
        age: Int?,
        height: Double?,
        weight: Double?,
        goal: String,
        activityLevel: String,
        gender: String? = nil
    ) async -> Bool {
        isLoading = true
        errorMessage = nil
        
        struct UpdateRequest: Codable {
            let name: String
            let age: Int?
            let height: Double?
            let weight: Double?
            let goal: String
            let activityLevel: String
            let gender: String?
            
            enum CodingKeys: String, CodingKey {
                case name
                case age
                case height
                case weight
                case goal
                case activityLevel = "activity_level"
                case gender
            }
        }
        
        struct Response: Codable {
            let ok: Bool
            let error: String?
        }
        
        let request = UpdateRequest(
            name: name,
            age: age,
            height: height,
            weight: weight,
            goal: goal,
            activityLevel: activityLevel,
            gender: gender
        )
        
        do {
            let response: Response = try await apiService.request(
                endpoint: Constants.API.updateProfile,
                method: "PUT",
                body: request
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
