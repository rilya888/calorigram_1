//
//  AnalysisViewModel.swift
//  Calorigram
//
//  ViewModel для анализа блюд
//

import Foundation
import UIKit

@MainActor
class AnalysisViewModel: ObservableObject {
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var analysisResult: AnalysisResult?
    @Published var selectedImageData: Data?
    
    private let apiService = APIService.shared
    
    func analyzeText(_ text: String) async {
        isLoading = true
        errorMessage = nil
        
        struct Request: Codable {
            let description: String
        }
        
        struct Response: Codable {
            let ok: Bool
            let result: Result?
            let error: String?
        }
        
        struct Result: Codable {
            let name: String
            let calories: Int
            let protein: Double
            let fat: Double
            let carbs: Double
        }
        
        do {
            let response: Response = try await apiService.request(
                endpoint: "/analysis/text",
                method: "POST",
                body: Request(description: text),
                requiresAuth: true
            )
            
            if response.ok, let result = response.result {
                analysisResult = AnalysisResult(
                    name: result.name,
                    calories: result.calories,
                    protein: result.protein,
                    fat: result.fat,
                    carbs: result.carbs
                )
            } else {
                errorMessage = response.error ?? "Ошибка анализа"
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    func analyzePhoto(data: Data) async {
        isLoading = true
        errorMessage = nil
        selectedImageData = data
        
        // Создаем multipart/form-data запрос
        guard let url = URL(string: Constants.apiBaseURL + "/analysis/photo") else {
            errorMessage = "Неверный URL"
            isLoading = false
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        // Добавляем токен авторизации
        if let token = KeychainService.shared.get(forKey: Constants.Keychain.accessToken) {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        // Создаем multipart body
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"photo.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(data)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        do {
            let (responseData, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                errorMessage = "Ошибка сервера"
                isLoading = false
                return
            }
            
            struct Response: Codable {
                let ok: Bool
                let result: Result?
                let error: String?
            }
            
            struct Result: Codable {
                let name: String
                let calories: Int
                let protein: Double
                let fat: Double
                let carbs: Double
            }
            
            let apiResponse = try JSONDecoder().decode(Response.self, from: responseData)
            
            if apiResponse.ok, let result = apiResponse.result {
                analysisResult = AnalysisResult(
                    name: result.name,
                    calories: result.calories,
                    protein: result.protein,
                    fat: result.fat,
                    carbs: result.carbs
                )
            } else {
                errorMessage = apiResponse.error ?? "Ошибка анализа"
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    func saveMeal() async {
        guard let result = analysisResult else { return }
        
        let viewModel = AddMealViewModel()
        let success = await viewModel.addMeal(
            mealType: "snack", // По умолчанию перекус, можно добавить выбор
            dishName: result.name,
            calories: result.calories,
            protein: result.protein,
            fat: result.fat,
            carbs: result.carbs
        )
        
        if success {
            analysisResult = nil
            selectedImageData = nil
        }
    }
}
