import Foundation
import PRLiftsCore

@MainActor
@Observable
final class WorkoutViewModel {

    // MARK: Phase

    enum Phase { case active, finishing, complete, syncFailed, synced }

    private(set) var phase: Phase = .active

    // MARK: State

    let workout: Workout
    var elapsedSeconds: Int = 0

    // Keyed by WorkoutExercise.id — weight and reps input per exercise
    var weightInputs: [UUID: String] = [:]
    var repsInputs: [UUID: String] = [:]

    // Which exercise just confirmed a saved set (auto-clears after 1.5 s)
    private(set) var setConfirmationExerciseID: UUID? = nil

    // Confirmation gate state
    var isShowingEmptyWorkoutAlert = false
    var isShowingCancelAlert = false

    // Keyed by WorkoutSet.id — true if this set triggered a PersonalRecord
    private(set) var prFlags: [UUID: Bool] = [:]

    private var timerTask: Task<Void, Never>?
    private let syncService: any WorkoutSyncServiceProtocol

    // MARK: Init

    init(workout: Workout, syncService: any WorkoutSyncServiceProtocol = StubWorkoutSyncService()) {
        self.workout = workout
        self.syncService = syncService
    }

    // MARK: Timer

    func startTimer() {
        timerTask?.cancel()
        let start = workout.startedAt
        timerTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(1))
                guard !Task.isCancelled else { break }
                self?.elapsedSeconds = Int(Date().timeIntervalSince(start))
            }
        }
    }

    func stopTimer() {
        timerTask?.cancel()
        timerTask = nil
    }

    var formattedElapsed: String {
        let h = elapsedSeconds / 3600
        let m = (elapsedSeconds % 3600) / 60
        let s = elapsedSeconds % 60
        if h > 0 {
            return String(format: "%d:%02d:%02d", h, m, s)
        }
        return String(format: "%02d:%02d", m, s)
    }

    // MARK: Exercises

    func addExercise(_ exercise: Exercise, insert: (WorkoutExercise) -> Void) {
        let we = WorkoutExercise(orderIndex: workout.exercises.count)
        we.workout = workout
        we.exercise = exercise
        workout.exercises.append(we)
        insert(we)
        weightInputs[we.id] = ""
        repsInputs[we.id] = ""
    }

    var sortedExercises: [WorkoutExercise] {
        workout.exercises.sorted { $0.orderIndex < $1.orderIndex }
    }

    // MARK: Set Logging

    @discardableResult
    func logSet(
        for workoutExercise: WorkoutExercise,
        weightUnit: WeightUnit,
        insert: (WorkoutSet) -> Void
    ) -> Bool {
        let repsStr = repsInputs[workoutExercise.id] ?? ""
        guard let reps = Int(repsStr), reps > 0 else { return false }

        let weightStr = weightInputs[workoutExercise.id] ?? ""
        let weight = Double(weightStr)

        let setNumber = workoutExercise.sets.count + 1
        let set = WorkoutSet(
            setNumber: setNumber,
            weight: weight,
            weightUnit: weight != nil ? weightUnit : nil,
            reps: reps,
            isCompleted: true
        )
        set.workoutExercise = workoutExercise
        workoutExercise.sets.append(set)
        insert(set)

        weightInputs[workoutExercise.id] = ""
        repsInputs[workoutExercise.id] = ""

        // Brief "Set saved" confirmation — Decision 93
        setConfirmationExerciseID = workoutExercise.id
        Task { [weak self, exerciseID = workoutExercise.id] in
            try? await Task.sleep(for: .milliseconds(1500))
            if self?.setConfirmationExerciseID == exerciseID {
                self?.setConfirmationExerciseID = nil
            }
        }

        return true
    }

    var totalSetCount: Int {
        workout.exercises.reduce(0) { $0 + $1.sets.count }
    }

    // MARK: Finish

    func requestFinish() {
        if totalSetCount == 0 {
            isShowingEmptyWorkoutAlert = true
        } else {
            confirmFinish()
        }
    }

    func confirmFinish() {
        let now = Date()
        workout.completedAt = now
        workout.durationSeconds = max(1, Int(now.timeIntervalSince(workout.startedAt)))
        workout.status = .completed
        workout.updatedAt = now
        stopTimer()
        phase = .finishing
        performSync()
    }

    func retrySync() {
        phase = .finishing
        performSync()
    }

    private func performSync() {
        Task { [weak self] in
            guard let self else { return }
            do {
                let flags = try await syncService.fetchPRFlags(for: workout.id)
                prFlags = flags
                phase = .complete
            } catch {
                phase = .syncFailed
            }
        }
    }

    // MARK: Cancel / Discard

    func requestCancel() {
        if totalSetCount == 0 {
            discard(delete: { _ in })
        } else {
            isShowingCancelAlert = true
        }
    }

    func discard(delete: (Workout) -> Void) {
        stopTimer()
        delete(workout)
        phase = .synced
    }
}
