//
//  CalorigramApp.swift
//  Calorigram
//
//  Главный файл приложения
//

import SwiftUI

@main
struct CalorigramApp: App {
    @StateObject private var authViewModel = AuthViewModel()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authViewModel)
        }
    }
}
