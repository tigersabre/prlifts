import SwiftUI
import SwiftData
import PRLiftsCore

struct WorkoutSummaryScreen: View {
    let viewModel: WorkoutViewModel
    let onDone: () -> Void

    @Environment(\.modelContext) private var modelContext
    @State private var insightViewModel = WorkoutInsightViewModel()

    var body: some View {
        ZStack(alignment: .bottom) {
            Color.prBackground.ignoresSafeArea()

            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: PRSpacing.medium) {
                    celebrationHeader
                    statsGrid
                    prStatusSection
                    exerciseList
                    if insightViewModel.phase != .idle {
                        aiInsightCard
                    }
                }
                .padding(.horizontal, PRSpacing.screenHorizontal)
                .padding(.top, PRSpacing.medium)
                .padding(.bottom, 90)
            }

            doneButton
        }
        .onChange(of: viewModel.phase) { _, newPhase in
            if newPhase == .complete {
                insightViewModel.trigger(
                    workoutID: viewModel.workout.id,
                    cachedInsight: viewModel.workout.aiInsightText
                ) { [self] text in
                    viewModel.workout.aiInsightText = text
                    try? modelContext.save()
                }
            }
        }
    }

    // MARK: Celebration Header

    private var celebrationHeader: some View {
        VStack(spacing: PRSpacing.xSmall) {
            Image(systemName: "trophy.fill")
                .font(.system(size: 48, weight: .semibold))
                .foregroundColor(Color.prCelebrationStart)
                .accessibilityHidden(true)

            Text("Workout complete!")
                .font(.prHeadlineLarge)
                .foregroundColor(.prTextPrimary)
                .accessibilityIdentifier("WorkoutCompleteHeading")

            if let name = viewModel.workout.name {
                Text(name)
                    .font(.prBody)
                    .foregroundColor(.prTextSecondary)
            }
        }
        .padding(.top, PRSpacing.large)
    }

    // MARK: Stats Grid

    private var statsGrid: some View {
        HStack(spacing: PRSpacing.xxSmall) {
            statCard(value: formattedDuration, label: "Duration")
            statCard(value: "\(viewModel.totalSetCount)", label: "Sets")
            statCard(value: "\(viewModel.workout.exercises.count)", label: "Exercises")
        }
    }

    private func statCard(value: String, label: String) -> some View {
        PRCard {
            VStack(spacing: PRSpacing.xxxSmall) {
                Text(value)
                    .font(.prDataLarge)
                    .foregroundColor(.prBrand)
                Text(label)
                    .font(.prCaption)
                    .foregroundColor(.prTextSecondary)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, PRSpacing.xxSmall)
        }
    }

    private var formattedDuration: String {
        let secs = viewModel.workout.durationSeconds ?? 0
        let totalMinutes = secs / 60
        let hours = totalMinutes / 60
        let minutes = totalMinutes % 60
        if hours > 0 {
            return "\(hours)h \(minutes)m"
        }
        return "\(totalMinutes)m"
    }

    // MARK: PR Status

    @ViewBuilder
    private var prStatusSection: some View {
        switch viewModel.phase {
        case .finishing:
            checkingPRsView
        case .syncFailed:
            syncFailedView
        default:
            EmptyView()
        }
    }

    private var checkingPRsView: some View {
        HStack(spacing: PRSpacing.xSmall) {
            ProgressView()
                .tint(.prBrand)
                .accessibilityHidden(true)
            Text("Checking for PRs\u{2026}")
                .font(.prBody)
                .foregroundColor(.prTextSecondary)
                .accessibilityIdentifier("CheckingPRsText")
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, PRSpacing.large)
    }

    private var syncFailedView: some View {
        VStack(spacing: PRSpacing.xSmall) {
            Text("Couldn't check for PRs")
                .font(.prCaption.weight(.semibold))
                .foregroundColor(.prTextSecondary)
            Button("Try Again") { viewModel.retrySync() }
                .font(.prCaption.weight(.medium))
                .foregroundColor(.prBrandLight)
                .accessibilityIdentifier("RetrySyncButton")
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, PRSpacing.small)
    }

    // MARK: Exercise List

    private var exerciseList: some View {
        VStack(spacing: PRSpacing.small) {
            ForEach(viewModel.sortedExercises) { workoutExercise in
                exerciseSection(workoutExercise)
            }
        }
    }

    private func exerciseSection(_ workoutExercise: WorkoutExercise) -> some View {
        let sorted = workoutExercise.sets.sorted { $0.setNumber < $1.setNumber }
        return PRCard {
            VStack(alignment: .leading, spacing: PRSpacing.xxSmall) {
                Text(workoutExercise.exercise?.name ?? "Exercise")
                    .font(.prHeadlineMedium)
                    .foregroundColor(.prTextPrimary)
                    .padding(.bottom, PRSpacing.xxxSmall)

                ForEach(sorted) { set in
                    summarySetRow(set)
                }
            }
        }
    }

    private func summarySetRow(_ set: WorkoutSet) -> some View {
        let isPR = viewModel.prFlags[set.id] == true
        return HStack {
            Text("Set \(set.setNumber)")
                .font(.prDataSmall)
                .foregroundColor(isPR ? .white : .prTextSecondary)
                .frame(width: 44, alignment: .leading)

            Spacer()

            Text(weightDisplay(set))
                .font(.prDataMedium)
                .foregroundColor(isPR ? .white : .prTextPrimary)

            Text(repsDisplay(set))
                .font(.prDataMedium)
                .foregroundColor(isPR ? .white : .prTextPrimary)
                .padding(.leading, PRSpacing.xxSmall)

            if isPR {
                Image(systemName: "star.fill")
                    .font(.system(size: 12))
                    .foregroundColor(.white)
                    .padding(.leading, PRSpacing.xxxSmall)
                    .accessibilityHidden(true)
            }
        }
        .padding(.horizontal, PRSpacing.xSmall)
        .padding(.vertical, PRSpacing.xxSmall)
        .background {
            if isPR {
                LinearGradient(
                    colors: [Color.prCelebrationStart, Color.prCelebrationEnd],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: PRRadius.small))
        .accessibilityLabel(setAccessibilityLabel(set, isPR: isPR))
    }

    private func weightDisplay(_ set: WorkoutSet) -> String {
        guard let w = set.weight else { return "—" }
        let unit = set.weightUnit?.rawValue ?? ""
        return "\(w.formatted(.number.precision(.fractionLength(0...1)))) \(unit)"
    }

    private func repsDisplay(_ set: WorkoutSet) -> String {
        guard let r = set.reps else { return "—" }
        return "× \(r)"
    }

    private func setAccessibilityLabel(_ set: WorkoutSet, isPR: Bool) -> String {
        var label = "Set \(set.setNumber): \(weightDisplay(set)), \(repsDisplay(set)) reps"
        if isPR { label += ", personal record" }
        return label
    }

    // MARK: AI Insight Card

    private var aiInsightCard: some View {
        PRCard {
            VStack(alignment: .leading, spacing: PRSpacing.xSmall) {
                insightCardHeader
                insightCardBody
            }
        }
    }

    private var insightCardHeader: some View {
        HStack(spacing: PRSpacing.xxSmall) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(.prBrandLight)
                .accessibilityHidden(true)
            Text("AI INSIGHT")
                .font(.prCaptionSmall.weight(.bold))
                .tracking(0.5)
                .foregroundColor(.prBrandLight)
                .accessibilityIdentifier("InsightCardHeader")
        }
    }

    @ViewBuilder
    private var insightCardBody: some View {
        switch insightViewModel.phase {
        case .idle:
            EmptyView()

        case .requesting, .polling:
            HStack(spacing: PRSpacing.xSmall) {
                ProgressView()
                    .tint(.prBrand)
                    .accessibilityHidden(true)
                Text("Generating your insight\u{2026}")
                    .font(.prBody)
                    .foregroundColor(.prTextSecondary)
                    .accessibilityIdentifier("InsightLoadingText")
            }

        case .complete(let text):
            Text(text)
                .font(.prBody)
                .foregroundColor(.prTextPrimary)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("InsightText")

        case .timeout:
            VStack(alignment: .leading, spacing: PRSpacing.xxSmall) {
                Text("Check back later")
                    .font(.prBody)
                    .foregroundColor(.prTextSecondary)
                    .accessibilityIdentifier("InsightTimeoutText")
                Button("Retry") {
                    insightViewModel.retry(
                        workoutID: viewModel.workout.id
                    ) { [self] text in
                        viewModel.workout.aiInsightText = text
                        try? modelContext.save()
                    }
                }
                .font(.prCaption.weight(.medium))
                .foregroundColor(.prBrandLight)
                .accessibilityIdentifier("InsightRetryButton")
            }

        case .rateLimited:
            Text("Come back later for your insight")
                .font(.prBody)
                .foregroundColor(.prTextSecondary)
                .accessibilityIdentifier("InsightRateLimitedText")

        case .offline:
            Text("No connection — will retry automatically")
                .font(.prBody)
                .foregroundColor(.prTextSecondary)
                .accessibilityIdentifier("InsightOfflineText")
        }
    }

    // MARK: Done Button

    private var doneButton: some View {
        VStack(spacing: 0) {
            Divider().overlay(Color.prBorder)
            PRButton(label: "Done") { onDone() }
                .padding(.horizontal, PRSpacing.screenHorizontal)
                .padding(.vertical, PRSpacing.small)
                .accessibilityIdentifier("SummaryDoneButton")
        }
        .background(Color.prBackground)
    }
}
