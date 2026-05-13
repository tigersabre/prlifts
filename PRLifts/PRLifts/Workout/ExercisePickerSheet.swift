import SwiftUI
import SwiftData
import PRLiftsCore

struct ExercisePickerSheet: View {
    @Environment(\.dismiss) private var dismiss
    @Query(sort: \Exercise.name) private var localExercises: [Exercise]

    @State private var searchText = ""
    @State private var remoteResults: [ExerciseSearchResult] = []
    @State private var isSearchingRemote = false
    @State private var remoteTask: Task<Void, Never>? = nil

    let onSelect: (Exercise) -> Void
    private let exerciseService: any ExerciseServiceProtocol

    init(
        onSelect: @escaping (Exercise) -> Void,
        exerciseService: any ExerciseServiceProtocol = StubExerciseService()
    ) {
        self.onSelect = onSelect
        self.exerciseService = exerciseService
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Color.prBackground.ignoresSafeArea()
                exerciseList
            }
            .navigationTitle("Add Exercise")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(.prBrandLight)
                }
            }
            .searchable(text: $searchText, placement: .navigationBarDrawer(displayMode: .always), prompt: "Search exercises")
            .onChange(of: searchText) { _, query in
                scheduleRemoteSearch(query: query)
            }
        }
        .presentationDetents([.large])
        .presentationDragIndicator(.visible)
        .presentationBackground(Color.prBackgroundSec)
    }

    // MARK: List

    private var exerciseList: some View {
        let filtered = filteredLocal
        return Group {
            if filtered.isEmpty && searchText.isEmpty {
                emptyLocalState
            } else {
                List {
                    if !filtered.isEmpty {
                        Section("Local library") {
                            ForEach(filtered) { exercise in
                                exerciseRow(exercise)
                            }
                        }
                    }
                    if !remoteResults.isEmpty {
                        Section("Search results") {
                            ForEach(remoteResults) { result in
                                remoteResultRow(result)
                            }
                        }
                    }
                    if isSearchingRemote {
                        Section {
                            HStack {
                                Spacer()
                                ProgressView()
                                Spacer()
                            }
                        }
                    }
                }
                .listStyle(.insetGrouped)
                .scrollContentBackground(.hidden)
            }
        }
    }

    private var filteredLocal: [Exercise] {
        guard !searchText.isEmpty else { return localExercises }
        return localExercises.filter {
            $0.name.localizedCaseInsensitiveContains(searchText)
        }
    }

    private var emptyLocalState: some View {
        VStack(spacing: PRSpacing.medium) {
            Image(systemName: "dumbbell")
                .font(.system(size: 40))
                .foregroundColor(.prTextTertiary)
                .accessibilityHidden(true)
            Text("No exercises yet")
                .font(.prHeadlineMedium)
                .foregroundColor(.prTextPrimary)
            Text("Search to find exercises from the library.")
                .font(.prBodySecondary)
                .foregroundColor(.prTextSecondary)
                .multilineTextAlignment(.center)
        }
        .padding(.horizontal, PRSpacing.large)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: Rows

    private func exerciseRow(_ exercise: Exercise) -> some View {
        Button {
            onSelect(exercise)
            dismiss()
        } label: {
            HStack {
                VStack(alignment: .leading, spacing: PRSpacing.xxxSmall) {
                    Text(exercise.name)
                        .font(.prBody)
                        .foregroundColor(.prTextPrimary)
                    Text("\(exercise.muscleGroup.displayName) · \(exercise.equipment.displayName)")
                        .font(.prCaption)
                        .foregroundColor(.prTextSecondary)
                }
                Spacer()
                Image(systemName: "plus.circle")
                    .foregroundColor(.prBrand)
                    .accessibilityHidden(true)
            }
        }
        .accessibilityLabel("\(exercise.name), \(exercise.muscleGroup.displayName)")
        .accessibilityHint("Double-tap to add")
    }

    private func remoteResultRow(_ result: ExerciseSearchResult) -> some View {
        Button {
            let exercise = Exercise(
                id: result.id,
                name: result.name,
                category: result.category,
                muscleGroup: result.muscleGroup,
                secondaryMuscleGroups: [],
                equipment: result.equipment
            )
            onSelect(exercise)
            dismiss()
        } label: {
            HStack {
                VStack(alignment: .leading, spacing: PRSpacing.xxxSmall) {
                    Text(result.name)
                        .font(.prBody)
                        .foregroundColor(.prTextPrimary)
                    Text("\(result.muscleGroup.displayName) · \(result.equipment.displayName)")
                        .font(.prCaption)
                        .foregroundColor(.prTextSecondary)
                }
                Spacer()
                Image(systemName: "plus.circle")
                    .foregroundColor(.prBrand)
                    .accessibilityHidden(true)
            }
        }
        .accessibilityLabel("\(result.name), \(result.muscleGroup.displayName)")
        .accessibilityHint("Double-tap to add")
    }

    // MARK: Remote search

    private func scheduleRemoteSearch(query: String) {
        remoteTask?.cancel()
        remoteResults = []
        guard !query.isEmpty else {
            isSearchingRemote = false
            return
        }
        guard filteredLocal.isEmpty else { return }

        isSearchingRemote = true
        remoteTask = Task {
            try? await Task.sleep(for: .milliseconds(400))
            guard !Task.isCancelled else { return }
            if let results = try? await exerciseService.search(query: query) {
                remoteResults = results
            }
            isSearchingRemote = false
        }
    }
}

// MARK: Display helpers

private extension MuscleGroup {
    var displayName: String {
        switch self {
        case .upperChest:   return "Upper chest"
        case .midChest:     return "Mid chest"
        case .lowerChest:   return "Lower chest"
        case .upperBack:    return "Upper back"
        case .lowerBack:    return "Lower back"
        case .shoulders:    return "Shoulders"
        case .biceps:       return "Biceps"
        case .triceps:      return "Triceps"
        case .quads:        return "Quads"
        case .hamstrings:   return "Hamstrings"
        case .calves:       return "Calves"
        case .glutes:       return "Glutes"
        case .abs:          return "Abs"
        case .obliques:     return "Obliques"
        case .fullBody:     return "Full body"
        }
    }
}

private extension ExerciseEquipment {
    var displayName: String {
        switch self {
        case .barbell:        return "Barbell"
        case .dumbbell:       return "Dumbbell"
        case .kettlebell:     return "Kettlebell"
        case .machine:        return "Machine"
        case .cable:          return "Cable"
        case .bodyweight:     return "Bodyweight"
        case .cardioMachine:  return "Cardio machine"
        case .other:          return "Other"
        }
    }
}
