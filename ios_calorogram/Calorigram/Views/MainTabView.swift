//
//  MainTabView.swift
//  Calorigram
//
//  Главная навигация с Tab Bar
//

import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem {
                    Label("Главная", systemImage: "house.fill")
                }
                .tag(0)
            
            DiaryView()
                .tabItem {
                    Label("Дневник", systemImage: "book.fill")
                }
                .tag(1)
            
            StatsView()
                .tabItem {
                    Label("Статистика", systemImage: "chart.bar.fill")
                }
                .tag(2)
            
            AnalysisView()
                .tabItem {
                    Label("Анализ", systemImage: "camera.fill")
                }
                .tag(3)
            
            ProfileView()
                .tabItem {
                    Label("Профиль", systemImage: "person.fill")
                }
                .tag(4)
        }
    }
}

struct MainTabView_Previews: PreviewProvider {
    static var previews: some View {
        MainTabView()
    }
}
