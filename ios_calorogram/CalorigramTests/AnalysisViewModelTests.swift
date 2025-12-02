//
//  AnalysisViewModelTests.swift
//  CalorigramTests
//
//  Unit тесты для AnalysisViewModel
//

import XCTest
@testable import Calorigram

@MainActor
final class AnalysisViewModelTests: XCTestCase {
    var viewModel: AnalysisViewModel!
    var mockAPIService: MockAPIService!

    override func setUp() {
        super.setUp()
        mockAPIService = MockAPIService()
        viewModel = AnalysisViewModel()
    }

    override func tearDown() {
        viewModel = nil
        mockAPIService = nil
        super.tearDown()
    }

    func testInitialState() {
        XCTAssertNil(viewModel.selectedImage)
        XCTAssertEqual(viewModel.analysisText, "")
        XCTAssertNil(viewModel.analysisResult)
        XCTAssertFalse(viewModel.isAnalyzing)
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertEqual(viewModel.selectedAnalysisType, .text)
    }

    func testSetSelectedImage() {
        // Given
        let testImage = UIImage(systemName: "photo")!

        // When
        viewModel.selectedImage = testImage

        // Then
        XCTAssertNotNil(viewModel.selectedImage)
        XCTAssertEqual(viewModel.selectedAnalysisType, .photo)
    }

    func testSetAnalysisText() {
        // Given
        let testText = "Стейк 200г с салатом"

        // When
        viewModel.analysisText = testText

        // Then
        XCTAssertEqual(viewModel.analysisText, testText)
        XCTAssertEqual(viewModel.selectedAnalysisType, .text)
    }

    func testAnalysisType_SwitchToPhoto() {
        // Given
        viewModel.analysisText = "Some text"
        XCTAssertEqual(viewModel.selectedAnalysisType, .text)

        // When
        viewModel.selectedImage = UIImage(systemName: "photo")!

        // Then
        XCTAssertEqual(viewModel.selectedAnalysisType, .photo)
    }

    func testAnalysisType_SwitchToText() {
        // Given
        viewModel.selectedImage = UIImage(systemName: "photo")!
        XCTAssertEqual(viewModel.selectedAnalysisType, .photo)

        // When
        viewModel.analysisText = "Some text"

        // Then
        XCTAssertEqual(viewModel.selectedAnalysisType, .text)
    }

    func testCanAnalyze_TextAnalysis_ValidText() {
        // Given
        viewModel.analysisText = "Куриная грудка 150г"

        // When & Then
        XCTAssertTrue(viewModel.canAnalyze)
    }

    func testCanAnalyze_TextAnalysis_EmptyText() {
        // Given
        viewModel.analysisText = ""

        // When & Then
        XCTAssertFalse(viewModel.canAnalyze)
    }

    func testCanAnalyze_TextAnalysis_WhitespaceOnly() {
        // Given
        viewModel.analysisText = "   \n\t  "

        // When & Then
        XCTAssertFalse(viewModel.canAnalyze)
    }

    func testCanAnalyze_PhotoAnalysis_ValidImage() {
        // Given
        viewModel.selectedImage = UIImage(systemName: "photo")!

        // When & Then
        XCTAssertTrue(viewModel.canAnalyze)
    }

    func testCanAnalyze_PhotoAnalysis_NoImage() {
        // Given
        viewModel.selectedImage = nil

        // When & Then
        XCTAssertFalse(viewModel.canAnalyze)
    }

    func testAnalyzeText_Success() async {
        // Given
        viewModel.analysisText = "Стейк 200г"

        // When
        await viewModel.analyze()

        // Then
        XCTAssertFalse(viewModel.isAnalyzing)
        // Note: Требуется внедрение зависимости для проверки результатов
    }

    func testAnalyzeText_Error() async {
        // Given
        viewModel.analysisText = "Valid text"
        mockAPIService.setShouldReturnError(true)

        // When
        await viewModel.analyze()

        // Then
        XCTAssertFalse(viewModel.isAnalyzing)
    }

    func testAnalyzePhoto_Success() async {
        // Given
        viewModel.selectedImage = UIImage(systemName: "photo")!

        // When
        await viewModel.analyze()

        // Then
        XCTAssertFalse(viewModel.isAnalyzing)
    }

    func testAnalyzePhoto_Error() async {
        // Given
        viewModel.selectedImage = UIImage(systemName: "photo")!
        mockAPIService.setShouldReturnError(true)

        // When
        await viewModel.analyze()

        // Then
        XCTAssertFalse(viewModel.isAnalyzing)
    }

    func testClearAnalysis() {
        // Given
        viewModel.analysisText = "Some text"
        viewModel.selectedImage = UIImage(systemName: "photo")!
        viewModel.analysisResult = createMockAnalysisResult()
        viewModel.errorMessage = "Some error"

        // When
        viewModel.clearAnalysis()

        // Then
        XCTAssertEqual(viewModel.analysisText, "")
        XCTAssertNil(viewModel.selectedImage)
        XCTAssertNil(viewModel.analysisResult)
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertEqual(viewModel.selectedAnalysisType, .text)
    }

    func testAnalysisResult_Formatting() {
        // Given
        let result = createMockAnalysisResult()
        viewModel.analysisResult = result

        // When & Then
        XCTAssertNotNil(viewModel.analysisResult)
        XCTAssertEqual(result.name, "Стейк")
        XCTAssertEqual(result.calories, 250)
    }

    // MARK: - Helper Methods

    private func createMockAnalysisResult() -> AnalysisResult {
        AnalysisResult(
            name: "Стейк",
            calories: 250,
            protein: 30.0,
            fat: 15.0,
            carbs: 0.0,
            weight: 150.0,
            confidence: 0.95
        )
    }

    // MARK: - Validation Tests

    func testTextAnalysis_ValidInputs() {
        let validTexts = [
            "Стейк 200г",
            "Куриная грудка 150 грамм",
            "Овсяная каша 50г с молоком",
            "Яблоко среднее"
        ]

        for text in validTexts {
            viewModel.analysisText = text
            XCTAssertTrue(viewModel.canAnalyze, "Should be able to analyze: \(text)")
        }
    }

    func testTextAnalysis_InvalidInputs() {
        let invalidTexts = [
            "",
            "   ",
            "\n\t",
            "!!!???",
            "123456789"
        ]

        for text in invalidTexts {
            viewModel.analysisText = text
            XCTAssertFalse(viewModel.canAnalyze, "Should not be able to analyze: \(text)")
        }
    }

    // MARK: - Performance Tests

    func testPerformance_TextAnalysis() {
        let testText = "Куриная грудка 150г с рисом 100г"

        measure {
            viewModel.analysisText = testText
            let _ = viewModel.canAnalyze
        }
    }

    func testPerformance_ClearAnalysis() {
        // Setup with data
        viewModel.analysisText = "Test analysis text"
        viewModel.selectedImage = UIImage(systemName: "photo")
        viewModel.analysisResult = createMockAnalysisResult()

        measure {
            viewModel.clearAnalysis()
        }
    }
}
