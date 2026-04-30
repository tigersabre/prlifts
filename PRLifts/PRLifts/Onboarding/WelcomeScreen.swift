import SwiftUI

struct WelcomeScreen: View {
    let onGetStarted: () -> Void
    let onSignIn: () -> Void

    private let benefits = [
        "Track every workout and every set",
        "Celebrate personal records automatically",
        "Get AI-powered insights after each session"
    ]

    var body: some View {
        ZStack {
            backgroundLayer
            VStack(spacing: 0) {
                Spacer()
                wordmarkSection
                taglineSection
                benefitsSection
                ctaSection
                Spacer(minLength: 0)
            }
            .padding(.horizontal, PRSpacing.screenHorizontal)
            termsCaption
        }
        .background(Color.prBackground.ignoresSafeArea())
    }

    private var backgroundLayer: some View {
        VStack {
            RadialGradient(
                colors: [Color.prBrand.opacity(0.22), Color.prBrand.opacity(0)],
                center: .top,
                startRadius: 0,
                endRadius: 300
            )
            .frame(height: 300)
            Spacer()
        }
        .ignoresSafeArea()
    }

    private var wordmarkSection: some View {
        VStack(spacing: 10) {
            HStack(spacing: 0) {
                Text("PR")
                    .font(.prDisplayLarge)
                    .foregroundColor(.prTextPrimary)
                Text("Lifts")
                    .font(.prDisplayLarge)
                    .foregroundColor(.prBrand)
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel("PRLifts")

            RoundedRectangle(cornerRadius: PRRadius.pill)
                .fill(Color.prBrand)
                .frame(width: 40, height: 3)
                .shadow(color: Color.prBrand.opacity(0.6), radius: 12, x: 0, y: 0)
        }
    }

    private var taglineSection: some View {
        Text("Track every lift.\nCelebrate every PR.")
            .font(.prDisplayMedium)
            .foregroundColor(.prTextPrimary)
            .multilineTextAlignment(.center)
            .padding(.top, PRSpacing.xLarge)
    }

    private var benefitsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            ForEach(benefits, id: \.self) { benefit in
                HStack(spacing: 12) {
                    ZStack {
                        Circle()
                            .fill(Color.prSuccess.opacity(0.15))
                            .frame(width: 26, height: 26)
                        Image(systemName: "checkmark")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.prSuccess)
                    }
                    Text(benefit)
                        .font(.prBodySecondary)
                        .foregroundColor(.prTextSecondary)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.top, PRSpacing.large)
    }

    private var ctaSection: some View {
        VStack(spacing: 14) {
            PRButton(label: "Get started", action: onGetStarted)
                .padding(.top, PRSpacing.xLarge)

            Button(action: onSignIn) {
                Text("Already have an account? ")
                    .foregroundColor(.prTextSecondary)
                + Text("Sign in")
                    .foregroundColor(.prBrandLight)
            }
            .font(.system(size: 14))
            .accessibilityLabel("Sign in to existing account")
        }
    }

    private var termsCaption: some View {
        VStack {
            Spacer()
            Text("By continuing, you agree to our Terms of Service and Privacy Policy.")
                .font(.prCaptionSmall)
                .foregroundColor(.prTextTertiary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, PRSpacing.screenHorizontal)
                .padding(.bottom, PRSpacing.small)
        }
    }
}

#Preview {
    WelcomeScreen(onGetStarted: {}, onSignIn: {})
}
