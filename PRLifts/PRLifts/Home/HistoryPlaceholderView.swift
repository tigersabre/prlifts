import SwiftUI

struct HistoryPlaceholderView: View {
    var body: some View {
        ZStack {
            Color.prBackground.ignoresSafeArea()
            VStack(spacing: PRSpacing.medium) {
                Image(systemName: "clock.arrow.circlepath")
                    .font(.system(size: 48))
                    .foregroundColor(.prTextTertiary)
                    .accessibilityHidden(true)
                Text("History")
                    .font(.prHeadlineLarge)
                    .foregroundColor(.prTextPrimary)
                Text("Your workout history will appear here.")
                    .font(.prBodySecondary)
                    .foregroundColor(.prTextSecondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal, PRSpacing.large)
        }
    }
}
