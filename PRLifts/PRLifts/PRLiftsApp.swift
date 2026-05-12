import SwiftUI
import SwiftData
import PRLiftsCore

@main
struct PRLiftsApp: App {
    init() {
        if ProcessInfo.processInfo.arguments.contains("ResetOnboarding") {
            UserDefaults.standard.removeObject(forKey: "hasCompletedOnboarding")
        }
        if ProcessInfo.processInfo.arguments.contains("SkipOnboarding") {
            UserDefaults.standard.set(true, forKey: "hasCompletedOnboarding")
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(
            // swiftlint:disable:next force_try
            try! PRLiftsSchema.makeContainer(
                inMemory: ProcessInfo.processInfo.arguments.contains("UITesting")
            )
        )
    }
}
