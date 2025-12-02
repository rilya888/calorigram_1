//
//  StatsView.swift
//  Calorigram
//
//  Экран статистики
//

import SwiftUI

struct StatsView: View {
    @StateObject private var viewModel = StatsViewModel()
    
    var body: some View {
        NavigationView {
            ZStack {
                if viewModel.isLoading && viewModel.weekStats == nil {
                    ProgressView()
                        .scaleEffect(1.5)
                } else if let errorMessage = viewModel.errorMessage {
                    ErrorView(
                        message: errorMessage,
                        onRetry: {
                            Task {
                                await viewModel.loadStats()
                            }
                        }
                    )
                } else if let weekStats = viewModel.weekStats {
                    ScrollView {
                        VStack(spacing: 20) {
                            WeekStatsView(stats: weekStats)
                                .padding()
                        }
                        .padding(.vertical)
                    }
                } else {
                    EmptyStateView(
                        message: "Нет данных за неделю",
                        onRetry: {
                            Task {
                                await viewModel.loadStats()
                            }
                        }
                    )
                }
            }
            .navigationTitle("Статистика")
            .refreshable {
                await viewModel.loadStats()
            }
            .task {
                if viewModel.weekStats == nil {
                    await viewModel.loadStats()
                }
            }
        }
    }
}

struct WeekStatsView: View {
    let stats: WeekStats
    
    var body: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Неделя")
                .font(.headline)
            
            HStack(alignment: .bottom, spacing: 8) {
                ForEach(stats.days) { day in
                    VStack(spacing: 4) {
                        // Столбик
                        GeometryReader { geometry in
                            let height = min(geometry.size.height * CGFloat(day.percentage / 100), geometry.size.height)
                            VStack {
                                Spacer()
                                Rectangle()
                                    .fill(colorForDay(day))
                                    .frame(height: height)
                                    .cornerRadius(4)
                            }
                        }
                        .frame(height: 100)
                        
                        // День недели
                        Text(day.day)
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        // Калории
                        Text("\(day.calories)")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .frame(height: 150)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    private func colorForDay(_ day: DayStats) -> Color {
        switch day.color {
        case "green": return .green
        case "yellow": return .yellow
        case "red": return .red
        default: return .gray
        }
    }
}

struct StatsView_Previews: PreviewProvider {
    static var previews: some View {
        StatsView()
    }
}
