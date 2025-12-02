//
//  APIServiceTests.swift
//  CalorigramTests
//
//  Unit тесты для APIService
//

import XCTest
@testable import Calorigram

final class APIServiceTests: XCTestCase {
    var apiService: APIService!
    
    override func setUp() {
        super.setUp()
        apiService = APIService.shared
    }
    
    override func tearDown() {
        apiService = nil
        super.tearDown()
    }
    
    func testAPIErrorDescriptions() {
        let invalidURL = APIError.invalidURL
        XCTAssertNotNil(invalidURL.errorDescription)
        XCTAssertEqual(invalidURL.errorDescription, "Неверный URL")
        
        let unauthorized = APIError.unauthorized
        XCTAssertNotNil(unauthorized.errorDescription)
        XCTAssertEqual(unauthorized.errorDescription, "Необходима авторизация")
        
        let serverError = APIError.serverError(500, "Internal Server Error")
        XCTAssertNotNil(serverError.errorDescription)
        XCTAssertTrue(serverError.errorDescription?.contains("500") ?? false)
    }
}

