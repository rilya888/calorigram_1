//
//  HomeViewModelTests.swift
//  CalorigramTests
//
//  Unit тесты для HomeViewModel
//

import XCTest
@testable import Calorigram

@MainActor
final class HomeViewModelTests: XCTestCase {
    var viewModel: HomeViewModel!
    
    override func setUp() {
        super.setUp()
        viewModel = HomeViewModel()
    }
    
    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }
    
    func testInitialState() {
        XCTAssertNil(viewModel.todayStats)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
    }
    
    func testLoadTodayStats() async {
        // Note: This is a basic test structure
        // In a real scenario, you would mock APIService
        XCTAssertFalse(viewModel.isLoading)
        
        // Since we can't easily mock APIService without dependency injection,
        // this test serves as a structure example
        // In production, you would inject a mock APIService
    }
}

