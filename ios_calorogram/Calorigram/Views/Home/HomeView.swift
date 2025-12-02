//
//  HomeView.swift
//  Calorigram
//
//  Главный экран с отображением калорий за сегодня
//

import SwiftUI

struct HomeView: View {
    @StateObject private var viewModel = HomeViewModel()
    @State private var showAddMealModal = false
    
    var body: some View {
        NavigationView {
            ZStack {
                if viewModel.isLoading && viewModel.todayStats == nil {
                    // Loading state
                    ProgressView()
                        .scaleEffect(1.5)
                } else if let errorMessage = viewModel.errorMessage {
                    // Error state
                    ErrorView(
                        message: errorMessage,
                        onRetry: {
                            Task {
                                await viewModel.loadTodayStats()
                            }
                        }
                    )
                } else if let stats = viewModel.todayStats {
                    // Content state
                    ScrollView {
                        VStack(spacing: 20) {
                            // Круговой прогресс-бар калорий
                            CaloriesProgressView(
                                consumed: stats.caloriesConsumed,
                                goal: stats.caloriesGoal
                            )
                            .padding()
                            
                            // Макросы
                            MacrosView(macros: stats.macros)
                                .padding(.horizontal)
                            
                            // Кнопка добавления приема пищи
                            Button(action: {
                                showAddMealModal = true
                            }) {
                                HStack {
                                    Image(systemName: "plus.circle.fill")
                                    Text("Добавить прием пищи")
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                            }
                            .buttonStyle(.borderedProminent)
                            .padding(.horizontal)
                        }
                        .padding(.vertical)
                    }
                } else {
                    // Empty state
                    EmptyStateView(
                        message: "Нет данных",
                        onRetry: {
                            Task {
                                await viewModel.loadTodayStats()
                            }
                        }
                    )
                }
            }
            .navigationTitle("Calorigram")
            .refreshable {
                await viewModel.loadTodayStats()
            }
            .task {
                if viewModel.todayStats == nil {
                    await viewModel.loadTodayStats()
                }
            }
            .sheet(isPresented: $showAddMealModal) {
                AddMealModal()
            }
            .overlay {
                if viewModel.isLoading && viewModel.todayStats != nil {
                    // Loading overlay when refreshing
                    Color.black.opacity(0.1)
                        .ignoresSafeArea()
                }
            }
        }
    }
}

struct CaloriesProgressView: View {
    let consumed: Int
    let goal: Int
    @State private var animatedPercentage: Double = 0
    
    private var percentage: Double {
        guard goal > 0 else { return 0 }
        return min(Double(consumed) / Double(goal), 1.0)
    }
    
    private var progressColor: Color {
        if percentage > 1.0 {
            return .red
        } else if percentage > 0.8 {
            return .orange
        } else {
            return .green
        }
    }
    
    var body: some View {
        VStack(spacing: 10) {
            ZStack {
                // Background circle
                Circle()
                    .stroke(Color.gray.opacity(0.2), lineWidth: 20)
                
                // Progress circle
                Circle()
                    .trim(from: 0, to: animatedPercentage)
                    .stroke(
                        progressColor,
                        style: StrokeStyle(lineWidth: 20, lineCap: .round)
                    )
                    .rotationEffect(.degrees(-90))
                    .animation(.spring(response: 1.0, dampingFraction: 0.8), value: animatedPercentage)
                
                // Center content
                VStack(spacing: 4) {
                    Text("\(consumed)")
                        .font(.system(size: 48, weight: .bold))
                        .foregroundColor(.primary)
                    Text("из \(goal) ккал")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    if goal > 0 {
                        Text("\(Int(percentage * 100))%")
                            .font(.caption2)
                            .foregroundColor(progressColor)
                            .padding(.top, 2)
                    }
                }
            }
            .frame(width: 200, height: 200)
            .onAppear {
                withAnimation {
                    animatedPercentage = percentage
                }
            }
            .onChange(of: percentage) { newValue in
                withAnimation {
                    animatedPercentage = newValue
                }
            }
        }
    }
}

struct MacrosView: View {
    let macros: Macros
    
    var body: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Макросы")
                .font(.headline)
                .foregroundColor(.primary)
            
            HStack(spacing: 15) {
                MacroItem(name: "Белки", value: macros.protein, unit: "г", color: .blue)
                MacroItem(name: "Жиры", value: macros.fat, unit: "г", color: .orange)
                MacroItem(name: "Углеводы", value: macros.carbs, unit: "г", color: .green)
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(.systemBackground))
                .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
        )
    }
}

struct MacroItem: View {
    let name: String
    let value: Double
    let unit: String
    let color: Color
    @State private var animatedValue: Double = 0
    
    var body: some View {
        VStack(spacing: 6) {
            Text(name)
                .font(.caption)
                .foregroundColor(.secondary)
                .textCase(.uppercase)
            
            Text("\(Int(animatedValue))")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(color)
                .contentTransition(.numericText())
            
            Text(unit)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(color.opacity(0.1))
        )
        .onAppear {
            withAnimation(.spring(response: 0.8, dampingFraction: 0.7)) {
                animatedValue = value
            }
        }
        .onChange(of: value) { newValue in
            withAnimation(.spring(response: 0.8, dampingFraction: 0.7)) {
                animatedValue = newValue
            }
        }
    }
}

// MARK: - Error View
struct ErrorView: View {
    let message: String
    let onRetry: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 50))
                .foregroundColor(.orange)
            
            Text("Ошибка")
                .font(.headline)
            
            Text(message)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            Button(action: onRetry) {
                HStack {
                    Image(systemName: "arrow.clockwise")
                    Text("Повторить")
                }
                .padding()
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}

// MARK: - Empty State View
struct EmptyStateView: View {
    let message: String
    let onRetry: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "tray")
                .font(.system(size: 50))
                .foregroundColor(.gray)
            
            Text(message)
                .font(.headline)
                .foregroundColor(.secondary)
            
            Button(action: onRetry) {
                HStack {
                    Image(systemName: "arrow.clockwise")
                    Text("Загрузить")
                }
                .padding()
            }
            .buttonStyle(.bordered)
        }
        .padding()
    }
}

struct HomeView_Previews: PreviewProvider {
    static var previews: some View {
        HomeView()
    }
}
