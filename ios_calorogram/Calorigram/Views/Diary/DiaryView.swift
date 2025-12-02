//
//  DiaryView.swift
//  Calorigram
//
//  Экран дневника с приемами пищи
//

import SwiftUI

struct DiaryView: View {
    @StateObject private var viewModel = DiaryViewModel()
    @State private var showAddMealModal = false
    
    var body: some View {
        NavigationView {
            ZStack {
                if viewModel.isLoading && viewModel.meals.isEmpty {
                    ProgressView()
                        .scaleEffect(1.5)
                } else if let errorMessage = viewModel.errorMessage {
                    ErrorView(
                        message: errorMessage,
                        onRetry: {
                            Task {
                                await viewModel.loadMeals()
                            }
                        }
                    )
                } else if viewModel.meals.isEmpty {
                    EmptyStateView(
                        message: "Нет приемов пищи за сегодня",
                        onRetry: {
                            Task {
                                await viewModel.loadMeals()
                            }
                        }
                    )
                } else {
                    List {
                        ForEach(viewModel.groupedMeals.keys.sorted(), id: \.self) { mealType in
                            Section(header: Text(mealTypeName(mealType))) {
                                ForEach(viewModel.groupedMeals[mealType] ?? []) { meal in
                                    MealRow(meal: meal)
                                }
                                .onDelete { indexSet in
                                    Task {
                                        await deleteMeals(at: indexSet, in: mealType)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Дневник")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showAddMealModal = true
                    }) {
                        Image(systemName: "plus")
                    }
                    .disabled(viewModel.isLoading)
                }
            }
            .refreshable {
                await viewModel.loadMeals()
            }
            .task {
                if viewModel.meals.isEmpty {
                    await viewModel.loadMeals()
                }
            }
            .sheet(isPresented: $showAddMealModal) {
                AddMealModal()
            }
        }
    }
    
    private func mealTypeName(_ type: String) -> String {
        switch type {
        case "breakfast": return "Завтрак"
        case "lunch": return "Обед"
        case "dinner": return "Ужин"
        case "snack": return "Перекус"
        default: return type.capitalized
        }
    }
    
    private func deleteMeals(at offsets: IndexSet, in mealType: String) async {
        guard let meals = viewModel.groupedMeals[mealType] else { return }
        let mealsToDelete = offsets.map { meals[$0] }
        
        for meal in mealsToDelete {
            if let mealId = meal.id {
                await viewModel.deleteMeal(id: mealId)
            }
        }
        
        await viewModel.loadMeals()
    }
}

struct MealRow: View {
    let meal: Meal
    
    var body: some View {
        HStack(spacing: 12) {
            // Icon
            Image(systemName: iconForMealType(meal.mealType))
                .font(.title3)
                .foregroundColor(colorForMealType(meal.mealType))
                .frame(width: 32, height: 32)
                .background(
                    Circle()
                        .fill(colorForMealType(meal.mealType).opacity(0.1))
                )
            
            VStack(alignment: .leading, spacing: 4) {
                Text(meal.dishName)
                    .font(.headline)
                    .foregroundColor(.primary)
                
                if let mealName = meal.mealName {
                    Text(mealName)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("\(meal.calories) ккал")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                HStack(spacing: 6) {
                    Label("\(Int(meal.protein))", systemImage: "p.circle.fill")
                        .font(.caption2)
                        .foregroundColor(.blue)
                    Label("\(Int(meal.fat))", systemImage: "f.circle.fill")
                        .font(.caption2)
                        .foregroundColor(.orange)
                    Label("\(Int(meal.carbs))", systemImage: "c.circle.fill")
                        .font(.caption2)
                        .foregroundColor(.green)
                }
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 4)
    }
    
    private func iconForMealType(_ type: String) -> String {
        switch type {
        case "breakfast": return "sunrise.fill"
        case "lunch": return "sun.max.fill"
        case "dinner": return "moon.fill"
        case "snack": return "applelogo"
        default: return "fork.knife"
        }
    }
    
    private func colorForMealType(_ type: String) -> Color {
        switch type {
        case "breakfast": return .orange
        case "lunch": return .yellow
        case "dinner": return .blue
        case "snack": return .green
        default: return .gray
        }
    }
}

struct DiaryView_Previews: PreviewProvider {
    static var previews: some View {
        DiaryView()
    }
}
