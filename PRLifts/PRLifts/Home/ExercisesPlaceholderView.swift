import SwiftUI

struct ExercisesPlaceholderView: View {
    var body: some View {
        ZStack {
            Color.prBackground.ignoresSafeArea()
            VStack(spacing: PRSpacing.medium) {
                Image(systemName: "list.bullet")
                    .font(.system(size: 48))
                    .foregroundColor(.prTextTertiary)
                    .accessibilityHidden(true)
                Text("Exercises")
                    .font(.prHeadlineLarge)
                    .foregroundColor(.prTextPrimary)
                Text("Browse and search exercises here.")
                    .font(.prBodySecondary)
                    .foregroundColor(.prTextSecondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal, PRSpacing.large)
        }
    }
}
