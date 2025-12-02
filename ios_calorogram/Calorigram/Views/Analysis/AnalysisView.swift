//
//  AnalysisView.swift
//  Calorigram
//
//  Экран анализа блюд по тексту и фото
//

import SwiftUI
import PhotosUI
import UIKit

struct AnalysisView: View {
    @StateObject private var viewModel = AnalysisViewModel()
    @State private var textInput = ""
    @State private var selectedPhoto: PhotosPickerItem?
    @State private var showImagePicker = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Анализ по тексту
                    VStack(alignment: .leading, spacing: 15) {
                        Text("Анализ по тексту")
                            .font(.headline)
                        
                        TextEditor(text: $textInput)
                            .frame(height: 100)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                            )
                            .overlay(
                                Group {
                                    if textInput.isEmpty {
                                        Text("Опишите блюдо...")
                                            .foregroundColor(.gray)
                                            .padding(.leading, 4)
                                            .padding(.top, 8)
                                            .allowsHitTesting(false)
                                    }
                                },
                                alignment: .topLeading
                            )
                        
                        Button(action: {
                            Task {
                                await viewModel.analyzeText(textInput)
                            }
                        }) {
                            if viewModel.isLoading {
                                ProgressView()
                                    .frame(maxWidth: .infinity)
                                    .padding()
                            } else {
                                Text("Проанализировать")
                                    .frame(maxWidth: .infinity)
                                    .padding()
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(textInput.isEmpty || viewModel.isLoading)
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    
                    // Анализ по фото
                    VStack(alignment: .leading, spacing: 15) {
                        Text("Анализ по фото")
                            .font(.headline)
                        
                        PhotosPicker(selection: $selectedPhoto, matching: .images) {
                            HStack {
                                Image(systemName: "photo")
                                Text("Выбрать фото")
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color(.systemGray5))
                            .cornerRadius(8)
                        }
                        .onChange(of: selectedPhoto) { newItem in
                            Task {
                                if let newItem = newItem {
                                    if let data = try? await newItem.loadTransferable(type: Data.self) {
                                        await viewModel.analyzePhoto(data: data)
                                    }
                                }
                            }
                        }
                        
                        if let imageData = viewModel.selectedImageData,
                           let uiImage = UIImage(data: imageData) {
                            Image(uiImage: uiImage)
                                .resizable()
                                .scaledToFit()
                                .frame(maxHeight: 200)
                                .cornerRadius(8)
                        }
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    
                    // Результаты анализа
                    if let result = viewModel.analysisResult {
                        AnalysisResultView(result: result) {
                            Task {
                                await viewModel.saveMeal()
                            }
                        }
                    }
                    
                    // Ошибка
                    if let errorMessage = viewModel.errorMessage {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                            .padding()
                    }
                }
                .padding()
            }
            .navigationTitle("Анализ блюд")
        }
    }
}

struct AnalysisResultView: View {
    let result: AnalysisResult
    let onSave: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Результат анализа")
                .font(.headline)
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Блюдо: \(result.name)")
                    .font(.subheadline)
                Text("Калории: \(result.calories) ккал")
                Text("Белки: \(Int(result.protein)) г")
                Text("Жиры: \(Int(result.fat)) г")
                Text("Углеводы: \(Int(result.carbs)) г")
            }
            
            Button(action: onSave) {
                Text("Сохранить в дневник")
                    .frame(maxWidth: .infinity)
                    .padding()
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct AnalysisResult {
    let name: String
    let calories: Int
    let protein: Double
    let fat: Double
    let carbs: Double
}

struct AnalysisView_Previews: PreviewProvider {
    static var previews: some View {
        AnalysisView()
    }
}
