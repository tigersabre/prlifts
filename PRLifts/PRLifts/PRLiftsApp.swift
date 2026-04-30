import SwiftUI

@main
struct PRLiftsApp: App {
    init() {
        if ProcessInfo.processInfo.arguments.contains("ResetOnboarding") {
            UserDefaults.standard.removeObject(forKey: "hasCompletedOnboarding")
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
