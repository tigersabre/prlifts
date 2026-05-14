import SwiftUI
import SwiftData
import PRLiftsCore

struct WorkoutScreen: View {
    @Environment(\.modelContext) private var modelContext
    @Query private var users: [User]
    @State private var viewModel: WorkoutViewModel
    @State private var isShowingExercisePicker = false

    private let onDismiss: () -> Void

    private var weightUnit: WeightUnit {
        users.first?.unitPreference ?? .lbs
    }

    init(workout: Workout, onDismiss: @escaping () -> Void) {
        _viewModel = State(wrappedValue: WorkoutViewModel(workout: workout))
        self.onDismiss = onDismiss
    }

    var body: some View {
        Group {
            if viewModel.phase == .finishing || viewModel.phase == .complete || viewModel.phase == .syncFailed {
                WorkoutSummaryScreen(viewModel: viewModel, onDone: onDismiss)
            } else {
                activeWorkoutContent
            }
        }
        .onChange(of: viewModel.phase) { _, phase in
            if phase == .synced { onDismiss() }
        }
    }

    private var activeWorkoutContent: some View {
        ZStack(alignment: .bottom) {
            Color.prBackground.ignoresSafeArea()

            VStack(spacing: 0) {
                navBar
                    .padding(.horizontal, PRSpacing.small)
                    .padding(.vertical, PRSpacing.xSmall)

                Divider().overlay(Color.prBorder)

                mainContent

                bottomBar
            }
        }
        .onAppear {
            modelContext.insert(viewModel.workout)
            viewModel.startTimer()
        }
        .onDisappear { viewModel.stopTimer() }
        .sheet(isPresented: $isShowingExercisePicker) {
            ExercisePickerSheet { exercise in
                viewModel.addExercise(exercise) { modelContext.insert($0) }
            }
        }
        .confirmationDialog(
            "No sets logged",
            isPresented: $viewModel.isShowingEmptyWorkoutAlert,
            titleVisibility: .visible
        ) {
            Button("Discard Workout", role: .destructive) {
                viewModel.discard { modelContext.delete($0) }
            }
            Button("Keep Logging", role: .cancel) {}
        } message: {
            Text("You haven't logged any sets. Discard this workout?")
        }
        .confirmationDialog(
            "Cancel workout?",
            isPresented: $viewModel.isShowingCancelAlert,
            titleVisibility: .visible
        ) {
            Button("Discard Workout", role: .destructive) {
                viewModel.discard { modelContext.delete($0) }
            }
            Button("Keep Going", role: .cancel) {}
        } message: {
            Text("All logged sets will be lost.")
        }
    }

    // MARK: Navigation bar

    private var navBar: some View {
        HStack {
            Button("Cancel") { viewModel.requestCancel() }
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.prBrandLight)
                .accessibilityIdentifier("CancelWorkoutButton")

            Spacer()

            Text(viewModel.workout.name ?? "Workout")
                .font(.prHeadlineMedium)
                .foregroundColor(.prTextPrimary)
                .lineLimit(1)

            Spacer()

            Text(viewModel.formattedElapsed)
                .font(.prDataSmall)
                .foregroundColor(.prSuccess)
                .monospacedDigit()
                .accessibilityLabel("Elapsed time \(viewModel.formattedElapsed)")
                .accessibilityIdentifier("WorkoutTimer")
        }
    }

    // MARK: Main content

    private var mainContent: some View {
        ScrollView(.vertical, showsIndicators: false) {
            LazyVStack(spacing: PRSpacing.small) {
                ForEach(viewModel.sortedExercises) { workoutExercise in
                    ExerciseSectionView(
                        workoutExercise: workoutExercise,
                        viewModel: viewModel,
                        weightUnit: weightUnit
                    )
                }
                addExerciseRow
            }
            .padding(.horizontal, PRSpacing.screenHorizontal)
            .padding(.top, PRSpacing.small)
            .padding(.bottom, PRSpacing.xxLarge)
        }
    }

    // MARK: Add exercise row

    private var addExerciseRow: some View {
        Button {
            isShowingExercisePicker = true
        } label: {
            HStack(spacing: PRSpacing.xxSmall) {
                Image(systemName: "plus.circle")
                    .font(.system(size: 18, weight: .medium))
                    .accessibilityHidden(true)
                Text("Add Exercise")
                    .font(.prBody.weight(.medium))
            }
            .foregroundColor(.prBrand)
            .frame(maxWidth: .infinity)
            .frame(height: 48)
            .overlay(
                RoundedRectangle(cornerRadius: PRRadius.large)
                    .strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [6, 4]))
                    .foregroundColor(.prBorder)
            )
        }
        .accessibilityIdentifier("AddExerciseButton")
        .accessibilityLabel("Add exercise")
    }

    // MARK: Bottom bar

    private var bottomBar: some View {
        VStack(spacing: 0) {
            Divider().overlay(Color.prBorder)
            PRButton(label: "Finish Workout") {
                viewModel.requestFinish()
            }
            .padding(.horizontal, PRSpacing.screenHorizontal)
            .padding(.vertical, PRSpacing.small)
            .accessibilityIdentifier("FinishWorkoutButton")
        }
        .background(Color.prBackground)
    }
}

// MARK: ExerciseSectionView

private struct ExerciseSectionView: View {
    @Environment(\.modelContext) private var modelContext

    let workoutExercise: WorkoutExercise
    @Bindable var viewModel: WorkoutViewModel
    let weightUnit: WeightUnit

    @FocusState private var weightFocused: Bool
    @FocusState private var repsFocused: Bool

    private var exerciseName: String {
        workoutExercise.exercise?.name ?? "Exercise"
    }

    private var unitLabel: String {
        weightUnit == .kg ? "kg" : "lbs"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: PRSpacing.xSmall) {
            exerciseHeader
            if !workoutExercise.sets.isEmpty {
                setTable
            }
            setInputCard
        }
    }

    // MARK: Exercise header

    private var exerciseHeader: some View {
        HStack {
            Text(exerciseName)
                .font(.prHeadlineMedium)
                .foregroundColor(.prTextPrimary)
            Spacer()
        }
        .padding(.top, PRSpacing.xxSmall)
    }

    // MARK: Set table

    private var setTable: some View {
        PRCard {
            VStack(spacing: 0) {
                setTableHeader
                let sorted = workoutExercise.sets.sorted { $0.setNumber < $1.setNumber }
                ForEach(sorted) { set in
                    setRow(set)
                }
            }
        }
    }

    private var setTableHeader: some View {
        HStack {
            Text("#")
                .frame(width: 28, alignment: .center)
            Spacer()
            Text("WEIGHT")
                .frame(minWidth: 80, alignment: .trailing)
            Text("REPS")
                .frame(width: 44, alignment: .trailing)
            Image(systemName: "checkmark")
                .frame(width: 28, alignment: .center)
                .accessibilityHidden(true)
        }
        .font(.prCaptionSmall.weight(.semibold))
        .foregroundColor(.prTextSecondary)
        .padding(.bottom, PRSpacing.xxSmall)
    }

    private func setRow(_ set: WorkoutSet) -> some View {
        HStack {
            Text("\(set.setNumber)")
                .font(.prDataSmall)
                .foregroundColor(.prTextSecondary)
                .frame(width: 28, alignment: .center)
            Spacer()
            Text(weightDisplay(set))
                .font(.prDataMedium)
                .foregroundColor(.prTextPrimary)
                .frame(minWidth: 80, alignment: .trailing)
            Text(repsDisplay(set))
                .font(.prDataMedium)
                .foregroundColor(.prTextPrimary)
                .frame(width: 44, alignment: .trailing)
            Image(systemName: "checkmark.circle.fill")
                .foregroundColor(.prSuccess)
                .frame(width: 28, alignment: .center)
                .accessibilityHidden(true)
        }
        .padding(.vertical, PRSpacing.xxxSmall)
        .accessibilityLabel("Set \(set.setNumber): \(weightDisplay(set)), \(repsDisplay(set)) reps")
    }

    private func weightDisplay(_ set: WorkoutSet) -> String {
        guard let w = set.weight else { return "—" }
        let unit = set.weightUnit?.rawValue ?? ""
        return "\(w.formatted(.number.precision(.fractionLength(0...1)))) \(unit)"
    }

    private func repsDisplay(_ set: WorkoutSet) -> String {
        guard let r = set.reps else { return "—" }
        return "\(r)"
    }

    // MARK: Set input card

    private var setInputCard: some View {
        PRCard {
            VStack(spacing: PRSpacing.xSmall) {
                setInputHeader
                HStack(spacing: PRSpacing.xSmall) {
                    weightField
                    repsField
                }
                PRButton(label: "Log Set", variant: .primary) {
                    viewModel.logSet(
                        for: workoutExercise,
                        weightUnit: weightUnit
                    ) { set in
                        modelContext.insert(set)
                    }
                }
                .frame(height: 44)
                .accessibilityIdentifier("LogSetButton")
            }
        }
    }

    private var setInputHeader: some View {
        HStack {
            Text("Set \(workoutExercise.sets.count + 1)")
                .font(.prCaption.weight(.semibold))
                .foregroundColor(.prTextSecondary)
            Spacer()
            if viewModel.setConfirmationExerciseID == workoutExercise.id {
                HStack(spacing: 4) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 13))
                        .foregroundColor(.prSuccess)
                        .accessibilityHidden(true)
                    Text("Set saved")
                        .font(.prCaption)
                        .foregroundColor(.prSuccess)
                }
                .transition(.opacity.combined(with: .scale(scale: 0.85)))
                .accessibilityLabel("Set saved")
            }
        }
        .animation(PRAnimation.quick, value: viewModel.setConfirmationExerciseID)
    }

    private var weightField: some View {
        VStack(alignment: .leading, spacing: PRSpacing.xxxSmall) {
            Text("Weight (\(unitLabel))")
                .font(.prCaptionSmall)
                .foregroundColor(.prTextTertiary)
            TextField("0", text: Binding(
                get: { viewModel.weightInputs[workoutExercise.id] ?? "" },
                set: { viewModel.weightInputs[workoutExercise.id] = $0 }
            ))
            .keyboardType(.decimalPad)
            .font(.prDataMedium)
            .multilineTextAlignment(.center)
            .focused($weightFocused)
            .prInputFieldStyle(isFocused: weightFocused, height: 50)
            .accessibilityLabel("Weight in \(unitLabel)")
            .accessibilityIdentifier("WeightInput")
        }
    }

    private var repsField: some View {
        VStack(alignment: .leading, spacing: PRSpacing.xxxSmall) {
            Text("Reps")
                .font(.prCaptionSmall)
                .foregroundColor(.prTextTertiary)
            TextField("0", text: Binding(
                get: { viewModel.repsInputs[workoutExercise.id] ?? "" },
                set: { viewModel.repsInputs[workoutExercise.id] = $0 }
            ))
            .keyboardType(.numberPad)
            .font(.prDataMedium)
            .multilineTextAlignment(.center)
            .focused($repsFocused)
            .prInputFieldStyle(isFocused: repsFocused, height: 50)
            .accessibilityLabel("Number of reps")
            .accessibilityIdentifier("RepsInput")
        }
    }
}
