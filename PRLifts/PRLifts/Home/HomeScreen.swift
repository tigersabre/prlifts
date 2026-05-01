import SwiftUI

struct HomeScreen: View {
    @State private var showComingSoon = false
    private let streak = 0

    var body: some View {
        ZStack {
            Color.prBackground.ignoresSafeArea()
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 10) {
                    headerRow
                        .padding(.top, PRSpacing.xxSmall)
                    streakCard
                    startWorkoutButton
                    statsGrid
                    recentPRsSection
                    futureSelfCard
                }
                .padding(.horizontal, PRSpacing.screenHorizontal)
                .padding(.bottom, PRSpacing.large)
            }
        }
        .alert("Coming Soon", isPresented: $showComingSoon) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("Workout logging is coming soon.")
        }
    }

    // MARK: Header

    private var headerRow: some View {
        HStack {
            Text("PRLifts")
                .font(.prHeadlineLarge)
                .foregroundColor(.prTextPrimary)
            Spacer()
            Circle()
                .fill(Color.prBackgroundTer)
                .frame(width: 32, height: 32)
                .overlay(
                    Image(systemName: "person.fill")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.prTextSecondary)
                )
                .accessibilityLabel("Profile avatar")
        }
    }

    // MARK: Streak Card

    private var streakCard: some View {
        HStack(spacing: PRSpacing.xSmall) {
            RoundedRectangle(cornerRadius: 14)
                .fill(Color.prBrand)
                .frame(width: 48, height: 48)
                .overlay(
                    Image(systemName: "flame.fill")
                        .font(.system(size: 22, weight: .semibold))
                        .foregroundColor(.white)
                )
                .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: PRSpacing.xxxSmall) {
                Text("Keep it going!")
                    .font(.prCaption)
                    .foregroundColor(.prTextSecondary)
                Text("\(streak)-day streak")
                    .font(.prHeadlineLarge)
                    .foregroundColor(.prTextPrimary)

                HStack(spacing: 4) {
                    ForEach(0..<7, id: \.self) { day in
                        RoundedRectangle(cornerRadius: 2)
                            .fill(day < streak ? Color.prBrand : Color.prBackgroundTer)
                            .frame(height: 4)
                            .frame(maxWidth: .infinity)
                    }
                }
                .accessibilityLabel("Streak progress: \(streak) of 7 days this week")
            }
        }
        .padding(PRSpacing.cardPadding)
        .background(
            LinearGradient(
                colors: [Color.prBrand.opacity(0.22), Color.prBrand.opacity(0.08)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .clipShape(RoundedRectangle(cornerRadius: PRRadius.large))
        .overlay(
            RoundedRectangle(cornerRadius: PRRadius.large)
                .stroke(Color.prBrand.opacity(0.40), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.12), radius: 4, x: 0, y: 2)
    }

    // MARK: Start Workout Button

    private var startWorkoutButton: some View {
        PRButton(label: "Start Workout", icon: "plus") {
            showComingSoon = true
        }
    }

    // MARK: Stats Grid

    private var statsGrid: some View {
        HStack(spacing: PRSpacing.xxSmall) {
            statCard(value: "0", label: "Workouts", valueColor: .prBrand)
            statCard(value: "0", label: "Personal Records", valueColor: .prAccent)
        }
    }

    private func statCard(value: String, label: String, valueColor: Color) -> some View {
        PRCard {
            VStack(spacing: PRSpacing.xxxSmall) {
                Text(value)
                    .font(.prDataLarge)
                    .foregroundColor(valueColor)
                Text(label)
                    .font(.prCaption)
                    .foregroundColor(.prTextSecondary)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, PRSpacing.xxSmall)
        }
    }

    // MARK: Recent PRs Section

    private var recentPRsSection: some View {
        VStack(spacing: PRSpacing.xSmall) {
            HStack {
                Text("Recent PRs")
                    .font(.prHeadlineLarge)
                    .foregroundColor(.prTextPrimary)
                Spacer()
                Button("See all →") {}
                    .font(.prCaption)
                    .foregroundColor(.prBrandLight)
                    .accessibilityLabel("See all personal records")
                    .disabled(true)
            }

            emptyPRsCard
        }
    }

    private var emptyPRsCard: some View {
        PRCard {
            VStack(spacing: PRSpacing.medium) {
                Image(systemName: "dumbbell.fill")
                    .font(.system(size: 36))
                    .foregroundColor(.prTextTertiary)
                    .accessibilityHidden(true)

                VStack(spacing: PRSpacing.xxxSmall) {
                    Text("Ready when you are.")
                        .font(.prHeadlineMedium)
                        .foregroundColor(.prTextPrimary)
                    Text("Tap to log your first workout.")
                        .font(.prBodySecondary)
                        .foregroundColor(.prTextSecondary)
                        .multilineTextAlignment(.center)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, PRSpacing.large)
        }
    }

    // MARK: Future Self Teaser

    private var futureSelfCard: some View {
        HStack {
            VStack(alignment: .leading, spacing: PRSpacing.xxxSmall) {
                Text("Future Self")
                    .font(.prCaptionSmall)
                    .fontWeight(.bold)
                    .textCase(.uppercase)
                    .tracking(0.5)
                    .foregroundColor(.prAccent)
                    .accessibilityLabel("Future Self")
                Text("See your future physique")
                    .font(.prHeadlineMedium)
                    .foregroundColor(.prTextPrimary)
                Text("Complete your profile to unlock AI-generated motivation.")
                    .font(.prCaption)
                    .foregroundColor(.prTextSecondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer()
            Image(systemName: "chevron.right")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.prTextTertiary)
                .accessibilityHidden(true)
        }
        .padding(PRSpacing.cardPadding)
        .background(
            LinearGradient(
                colors: [
                    Color.prCelebrationStart.opacity(0.10),
                    Color.prCelebrationEnd.opacity(0.06)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .clipShape(RoundedRectangle(cornerRadius: PRRadius.large))
        .overlay(
            RoundedRectangle(cornerRadius: PRRadius.large)
                .stroke(Color.prAccent.opacity(0.30), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.12), radius: 4, x: 0, y: 2)
    }
}

#Preview {
    HomeScreen()
        .preferredColorScheme(.dark)
}

#Preview("Light") {
    HomeScreen()
        .preferredColorScheme(.light)
}
