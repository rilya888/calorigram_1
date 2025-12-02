//
//  NotificationService.swift
//  Calorigram
//
//  Сервис для локальных уведомлений
//

import Foundation
import UserNotifications

class NotificationService {
    static let shared = NotificationService()
    
    private init() {}
    
    // MARK: - Request Authorization
    
    func requestAuthorization() async -> Bool {
        do {
            let granted = try await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge])
            return granted
        } catch {
            print("Error requesting notification authorization: \(error)")
            return false
        }
    }
    
    // MARK: - Schedule Meal Reminders
    
    func scheduleMealReminders(enabled: Bool, times: [Date]) {
        let center = UNUserNotificationCenter.current()
        
        // Удаляем все существующие напоминания о приемах пищи
        center.removePendingNotificationRequests(withIdentifiers: ["meal_reminder"])
        
        guard enabled else { return }
        
        // Создаем уведомления для каждого времени
        for (index, time) in times.enumerated() {
            let content = UNMutableNotificationContent()
            content.title = "Время приема пищи"
            content.body = "Не забудьте добавить прием пищи в дневник"
            content.sound = .default
            content.badge = 1
            
            // Создаем триггер на основе времени
            let calendar = Calendar.current
            let components = calendar.dateComponents([.hour, .minute], from: time)
            
            var dateComponents = DateComponents()
            dateComponents.hour = components.hour
            dateComponents.minute = components.minute
            
            let trigger = UNCalendarNotificationTrigger(dateMatching: dateComponents, repeats: true)
            
            let request = UNNotificationRequest(
                identifier: "meal_reminder_\(index)",
                content: content,
                trigger: trigger
            )
            
            center.add(request) { error in
                if let error = error {
                    print("Error scheduling notification: \(error)")
                }
            }
        }
    }
    
    // MARK: - Cancel All Reminders
    
    func cancelAllReminders() {
        let center = UNUserNotificationCenter.current()
        center.removeAllPendingNotificationRequests()
    }
    
    // MARK: - Get Pending Notifications
    
    func getPendingNotifications() async -> [UNNotificationRequest] {
        return await UNUserNotificationCenter.current().pendingNotificationRequests()
    }
}

