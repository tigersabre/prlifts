import SwiftUI

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
    }
}
