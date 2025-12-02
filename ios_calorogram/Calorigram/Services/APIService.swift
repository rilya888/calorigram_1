//
//  APIService.swift
//  Calorigram
//
//  Базовый сервис для HTTP запросов к API
//

import Foundation

enum APIError: Error, LocalizedError {
    case invalidURL
    case noData
    case decodingError
    case serverError(Int, String)
    case unauthorized
    case networkError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Неверный URL"
        case .noData:
            return "Нет данных"
        case .decodingError:
            return "Ошибка декодирования"
        case .serverError(let code, let message):
            // Пытаемся извлечь понятное сообщение из JSON
            if let jsonData = message.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
               let detail = json["detail"] as? String {
                // Обрабатываем специфичные ошибки
                if detail.contains("already registered") || detail.contains("уже зарегистрирован") {
                    return "Этот email уже зарегистрирован. Попробуйте войти."
                }
                if detail.contains("invalid") || detail.contains("неверный") {
                    return detail
                }
                return detail
            }
            return "Ошибка сервера \(code): \(message)"
        case .unauthorized:
            return "Необходима авторизация"
        case .networkError(let error):
            return "Ошибка сети: \(error.localizedDescription)"
        }
    }
}

class APIService {
    static let shared = APIService()
    
    private let baseURL: String
    private let keychainService = KeychainService.shared
    
    init(baseURL: String = Constants.apiBaseURL) {
        self.baseURL = baseURL
    }
    
    // MARK: - Generic Request Method
    
    func request<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Encodable? = nil,
        requiresAuth: Bool = true,
        maxRetries: Int = 3
    ) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Добавляем токен авторизации если требуется
        if requiresAuth {
            if let token = keychainService.get(forKey: Constants.Keychain.accessToken) {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            } else {
                throw APIError.unauthorized
            }
        }
        
        // Добавляем body если есть
        if let body = body {
            do {
                request.httpBody = try JSONEncoder().encode(body)
            } catch {
                throw APIError.decodingError
            }
        }
        
        // Выполняем запрос с retry логикой
        var lastError: Error?
        
        // Логируем запрос для отладки
        print("🌐 API Request: \(method) \(baseURL + endpoint)")
        if let body = body, let bodyData = try? JSONEncoder().encode(body) {
            print("📤 Request body: \(String(data: bodyData, encoding: .utf8) ?? "nil")")
        }
        
        for attempt in 0..<maxRetries {
            do {
                let (data, response) = try await URLSession.shared.data(for: request)
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    print("❌ Invalid HTTP response")
                    throw APIError.networkError(NSError(domain: "APIService", code: -1))
                }
                
                print("📥 Response: Status \(httpResponse.statusCode)")
                if let responseString = String(data: data, encoding: .utf8) {
                    print("📥 Response body: \(responseString.prefix(500))")
                }
                
                // Обрабатываем ошибки
                if httpResponse.statusCode == 401 {
                    // Пытаемся обновить токен
                    if let refreshed = try? await refreshToken() {
                        // Повторяем запрос с новым токеном
                        request.setValue("Bearer \(refreshed)", forHTTPHeaderField: "Authorization")
                        let (retryData, retryResponse) = try await URLSession.shared.data(for: request)
                        
                        guard let retryHttpResponse = retryResponse as? HTTPURLResponse,
                              (200...299).contains(retryHttpResponse.statusCode) else {
                            throw APIError.unauthorized
                        }
                        
                        do {
                            return try JSONDecoder().decode(T.self, from: retryData)
                        } catch {
                            throw APIError.decodingError
                        }
                    } else {
                        throw APIError.unauthorized
                    }
                }
                
                guard (200...299).contains(httpResponse.statusCode) else {
                    let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
                    print("❌ Server error \(httpResponse.statusCode): \(errorMessage)")
                    throw APIError.serverError(httpResponse.statusCode, errorMessage)
                }
                
                do {
                    let decoded = try JSONDecoder().decode(T.self, from: data)
                    print("✅ Successfully decoded response")
                    return decoded
                } catch {
                    print("❌ Decoding error: \(error)")
                    print("❌ Response data: \(String(data: data, encoding: .utf8) ?? "nil")")
                    throw APIError.decodingError
                }
            } catch let error as APIError {
                print("❌ APIError on attempt \(attempt + 1)/\(maxRetries): \(error.localizedDescription)")
                
                // Для некоторых ошибок не делаем retry
                if case .unauthorized = error {
                    throw error
                }
                if case .decodingError = error {
                    throw error
                }
                
                lastError = error
                
                // Если это последняя попытка, выбрасываем ошибку
                if attempt == maxRetries - 1 {
                    throw error
                }
                
                // Ждем перед следующей попыткой (exponential backoff)
                let delay = pow(2.0, Double(attempt)) // 1s, 2s, 4s...
                print("⏳ Retrying in \(delay)s...")
                try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                
            } catch {
                print("❌ Network error on attempt \(attempt + 1)/\(maxRetries): \(error.localizedDescription)")
                lastError = error
                
                // Если это последняя попытка, выбрасываем ошибку
                if attempt == maxRetries - 1 {
                    throw APIError.networkError(error)
                }
                
                // Ждем перед следующей попыткой
                let delay = pow(2.0, Double(attempt))
                print("⏳ Retrying in \(delay)s...")
                try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
            }
        }
        
        // Если дошли сюда, выбрасываем последнюю ошибку
        if let lastError = lastError {
            throw lastError
        }
        
        throw APIError.networkError(NSError(domain: "APIService", code: -1))
    }
    
    // MARK: - Token Refresh
    
    private func refreshToken() async throws -> String? {
        guard let refreshToken = keychainService.get(forKey: Constants.Keychain.refreshToken) else {
            return nil
        }
        
        let request = RefreshTokenRequest(refreshToken: refreshToken)
        
        do {
            let response: RefreshTokenResponse = try await self.request(
                endpoint: Constants.API.refreshToken,
                method: "POST",
                body: request,
                requiresAuth: false
            )
            
            // Сохраняем новый токен
            _ = keychainService.save(response.accessToken, forKey: Constants.Keychain.accessToken)
            
            return response.accessToken
        } catch {
            // Если refresh не удался, очищаем токены
            keychainService.clearAll()
            return nil
        }
    }
}

