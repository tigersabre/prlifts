import SwiftUI

struct ContentView: View {
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false

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
