//
//  APIServiceProtocol.swift
//  Calorigram
//
//  Протокол для APIService для возможности тестирования
//

import Foundation

protocol APIServiceProtocol {
    func request<T: Decodable>(
        endpoint: String,
        method: String,
        body: Encodable?,
        headers: [String: String]?,
        retryCount: Int,
        retryDelay: TimeInterval
    ) async throws -> T

    func request(
        endpoint: String,
        method: String,
        body: Encodable?,
        headers: [String: String]?,
        retryCount: Int,
        retryDelay: TimeInterval
    ) async throws
}
