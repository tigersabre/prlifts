import SwiftUI

struct ContentView: View {
    @State private var hasCompletedOnboarding: Bool =
        UserDefaults.standard.bool(forKey: "hasCompletedOnboarding")

    var body: some View {
        if hasCompletedOnboarding {
            MainTabView()
        } else {
            OnboardingCoordinator {
                hasCompletedOnboarding = true
            }
        }
    }
}

#Preview {
    ContentView()
}
