import SwiftUI

struct SignInScreen: View {
    @Bindable var viewModel: OnboardingViewModel
    let onSignedIn: () -> Void

    @FocusState private var emailFocused: Bool

    var body: some View {
        ZStack {
            Color.prBackground.ignoresSafeArea()
            VStack(alignment: .leading, spacing: 0) {
                titleSection
                authButtons
                divider
                emailSection
                errorBanner
                Spacer()
            }
            .padding(.horizontal, PRSpacing.screenHorizontal)
            termsCaption
        }
        .navigationBarHidden(true)
    }

    private var titleSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Sign in to PRLifts")
                .font(.prDisplayMedium)
                .foregroundColor(.prTextPrimary)
                .padding(.top, 12)
            Text("Create an account or sign in to continue")
                .font(.prBodySecondary)
                .foregroundColor(.prTextSecondary)
        }
    }

    private var authButtons: some View {
        VStack(spacing: 12) {
            appleButton
            googleButton
        }
        .padding(.top, PRSpacing.xLarge)
    }

    private var appleButton: some View {
        Button {
            Task {
                if await viewModel.signInWithApple() != nil {
                    onSignedIn()
                }
            }
        } label: {
            HStack(spacing: 8) {
                if viewModel.isLoading {
                    ProgressView().tint(Color.prBackground)
                } else {
                    Image(systemName: "apple.logo")
                        .font(.system(size: 18, weight: .medium))
                    Text("Continue with Apple")
                        .font(.prButtonPrimary)
                }
            }
            .foregroundColor(Color.prBackground)
            .frame(maxWidth: .infinity)
            .frame(height: 52)
            .background(Color.prTextPrimary)
            .clipShape(Capsule())
        }
        .disabled(viewModel.isLoading)
        .accessibilityLabel("Sign in with Apple")
    }

    private var googleButton: some View {
        Button {
            Task {
                if await viewModel.signInWithGoogle() != nil {
                    onSignedIn()
                }
            }
        } label: {
            HStack(spacing: 8) {
                Text("G")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(Color(red: 0.259, green: 0.522, blue: 0.957))
                Text("Continue with Google")
                    .font(.prButtonPrimary)
                    .foregroundColor(.prTextPrimary)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 52)
            .background(Color.prBackgroundSec)
            .clipShape(Capsule())
            .overlay(Capsule().stroke(Color.prBorder, lineWidth: 1.5))
        }
        .disabled(viewModel.isLoading)
        .accessibilityLabel("Sign in with Google")
    }

    private var divider: some View {
        HStack(spacing: 12) {
            Rectangle().fill(Color.prBorder).frame(height: 1)
            Text("or continue with email")
                .font(.system(size: 13))
                .foregroundColor(.prTextTertiary)
                .fixedSize()
            Rectangle().fill(Color.prBorder).frame(height: 1)
        }
        .padding(.vertical, PRSpacing.medium)
    }

    private var emailSection: some View {
        VStack(spacing: 12) {
            TextField("your@email.com", text: $viewModel.email)
                .keyboardType(.emailAddress)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .font(.prBody)
                .foregroundColor(.prTextPrimary)
                .focused($emailFocused)
                .prInputFieldStyle(isFocused: emailFocused, height: 48)
                .accessibilityLabel("Email address")

            PRButton(
                label: "Continue",
                isLoading: viewModel.isLoading,
                isDisabled: !viewModel.emailContinueEnabled || viewModel.isLoading
            ) {
                Task {
                    emailFocused = false
                    if await viewModel.continueWithEmail() != nil {
                        onSignedIn()
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var errorBanner: some View {
        if let message = viewModel.errorMessage {
            HStack(spacing: 10) {
                Image(systemName: "exclamationmark.circle.fill")
                    .foregroundColor(.prError)
                Text(message)
                    .font(.prBodySecondary)
                    .foregroundColor(.prError)
                    .fixedSize(horizontal: false, vertical: true)
                Spacer()
            }
            .padding(12)
            .background(Color.prError.opacity(0.10))
            .overlay(
                RoundedRectangle(cornerRadius: PRRadius.medium)
                    .stroke(Color.prError.opacity(0.40), lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: PRRadius.medium))
            .padding(.top, 12)
            .transition(.move(edge: .bottom).combined(with: .opacity))
            .animation(PRAnimation.sheet, value: viewModel.errorMessage)
        }
    }

    private var termsCaption: some View {
        VStack {
            Spacer()
            HStack(spacing: 4) {
                Text("By signing in, you agree to our")
                    .foregroundColor(.prTextTertiary)
                Button("Terms") {}
                    .foregroundColor(.prBrandLight)
                Text("and")
                    .foregroundColor(.prTextTertiary)
                Button("Privacy Policy") {}
                    .foregroundColor(.prBrandLight)
            }
            .font(.system(size: 12))
            .padding(.bottom, PRSpacing.small)
        }
    }
}
