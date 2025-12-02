//
//  RemindersSettingsModal.swift
//  Calorigram
//
//  Модальное окно настроек напоминаний
//

import SwiftUI

struct RemindersSettingsModal: View {
    @Environment(\.dismiss) var dismiss
    @State private var remindersEnabled = false
    @State private var breakfastTime = Date()
    @State private var lunchTime = Date()
    @State private var dinnerTime = Date()
    
    private let notificationService = NotificationService.shared
    
    var body: some View {
        NavigationView {
            Form {
                Section {
                    Toggle("Включить напоминания", isOn: $remindersEnabled)
                        .onChange(of: remindersEnabled) { newValue in
                            if newValue {
                                Task {
                                    await requestNotificationPermission()
                                }
                            } else {
                                notificationService.cancelAllReminders()
                            }
                        }
                } header: {
                    Text("Напоминания о приемах пищи")
                } footer: {
                    Text("Получайте уведомления о времени приема пищи")
                }
                
                if remindersEnabled {
                    Section("Время напоминаний") {
                        DatePicker("Завтрак", selection: $breakfastTime, displayedComponents: .hourAndMinute)
                        DatePicker("Обед", selection: $lunchTime, displayedComponents: .hourAndMinute)
                        DatePicker("Ужин", selection: $dinnerTime, displayedComponents: .hourAndMinute)
                    }
                }
            }
            .navigationTitle("Напоминания")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Отмена") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Сохранить") {
                        saveReminders()
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func requestNotificationPermission() async {
        let granted = await notificationService.requestAuthorization()
        if !granted {
            remindersEnabled = false
        }
    }
    
    private func saveReminders() {
        if remindersEnabled {
            let times = [breakfastTime, lunchTime, dinnerTime]
            notificationService.scheduleMealReminders(enabled: true, times: times)
        } else {
            notificationService.cancelAllReminders()
        }
    }
}

struct RemindersSettingsModal_Previews: PreviewProvider {
    static var previews: some View {
        RemindersSettingsModal()
    }
}

