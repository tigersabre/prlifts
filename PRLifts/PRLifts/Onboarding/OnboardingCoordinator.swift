import SwiftUI

enum OnboardingStep: Hashable {
    case signIn
    case displayName
    case unitPreference
}

struct OnboardingCoordinator: View {
    @State private var path = NavigationPath()
    @State private var viewModel = OnboardingViewModel()
    let onComplete: () -> Void

    var body: some View {
        NavigationStack(path: $path) {
            WelcomeScreen(
                onGetStarted: { path.append(OnboardingStep.signIn) },
                onSignIn: { path.append(OnboardingStep.signIn) }
            )
            .navigationDestination(for: OnboardingStep.self) { step in
                switch step {
                case .signIn:
                    SignInScreen(viewModel: viewModel) {
                        path.append(OnboardingStep.displayName)
                    }
                case .displayName:
                    DisplayNameScreen(
                        viewModel: viewModel,
                        onBack: { path.removeLast() },
                        onContinue: { path.append(OnboardingStep.unitPreference) }
                    )
                case .unitPreference:
                    UnitPreferenceScreen(
                        viewModel: viewModel,
                        onBack: { path.removeLast() },
                        onContinue: {
                            UserDefaults.standard.set(true, forKey: "hasCompletedOnboarding")
                            onComplete()
                        }
                    )
                }
            }
        }
        .tint(.prBrandLight)
    }
}
