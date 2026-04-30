import SwiftUI

struct DisplayNameScreen: View {
    @Bindable var viewModel: OnboardingViewModel
    let onBack: () -> Void
    let onContinue: () -> Void

    @FocusState private var fieldFocused: Bool
    @State private var showValidationError: Bool = false

    var body: some View {
        ZStack {
            Color.prBackground.ignoresSafeArea()
            VStack(alignment: .leading, spacing: 0) {
                navBar
                PRProgressDots(total: 4, current: 3)
                    .padding(.top, PRSpacing.large)
                headline
                fieldSection
                Spacer()
                PRButton(
                    label: "Continue",
                    isDisabled: !viewModel.isDisplayNameValid
                ) {
                    if viewModel.isDisplayNameValid {
                        onContinue()
                    } else {
                        showValidationError = true
                    }
                }
                .padding(.bottom, PRSpacing.xLarge)
            }
            .padding(.horizontal, PRSpacing.screenHorizontal)
            stepLabel
        }
        .navigationBarHidden(true)
        .onAppear { fieldFocused = true }
    }

    private var navBar: some View {
        HStack {
            Button(action: onBack) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(.prBrandLight)
                    .frame(width: PRSpacing.minimumTouchTarget, height: PRSpacing.minimumTouchTarget)
            }
            .accessibilityLabel("Back")
            Spacer()
        }
        .frame(height: 50)
    }

    private var headline: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("What should we\ncall you?")
                .font(.prDisplayMedium)
                .foregroundColor(.prTextPrimary)
            Text("This is how you'll appear across your PRLifts profile.")
                .font(.prBodySecondary)
                .foregroundColor(.prTextSecondary)
        }
        .padding(.top, PRSpacing.xSmall)
    }

    private var fieldSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Display name")
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(.prTextSecondary)
                .padding(.top, PRSpacing.xLarge)

            TextField("Your name", text: $viewModel.displayName)
                .font(.prBody)
                .foregroundColor(.prTextPrimary)
                .focused($fieldFocused)
                .onChange(of: viewModel.displayName) { _, newValue in
                    if newValue.count > 50 {
                        viewModel.displayName = String(newValue.prefix(50))
                    }
                    showValidationError = false
                }
                .prInputFieldStyle(isFocused: fieldFocused)
                .accessibilityLabel("Display name, \(viewModel.displayName.count) of 50 characters")

            if showValidationError {
                Text("Please enter a display name")
                    .font(.prCaption)
                    .foregroundColor(.prError)
                    .transition(.opacity)
            } else {
                Text("Up to 50 characters")
                    .font(.system(size: 12))
                    .foregroundColor(.prTextTertiary)
            }
        }
        .animation(PRAnimation.quick, value: showValidationError)
    }

    private var stepLabel: some View {
        VStack {
            Spacer()
            Text("Step 3 of 4")
                .font(.system(size: 14))
                .foregroundColor(.prTextTertiary)
                .padding(.bottom, PRSpacing.small)
        }
    }
}
