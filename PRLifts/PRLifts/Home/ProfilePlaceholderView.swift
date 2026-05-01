import SwiftUI

struct ProfilePlaceholderView: View {
    var body: some View {
        ZStack {
            Color.prBackground.ignoresSafeArea()
            VStack(spacing: PRSpacing.medium) {
                Image(systemName: "person.circle")
                    .font(.system(size: 48))
                    .foregroundColor(.prTextTertiary)
                    .accessibilityHidden(true)
                Text("Profile")
                    .font(.prHeadlineLarge)
                    .foregroundColor(.prTextPrimary)
                Text("Your profile and settings will appear here.")
                    .font(.prBodySecondary)
                    .foregroundColor(.prTextSecondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal, PRSpacing.large)
        }
    }
}
