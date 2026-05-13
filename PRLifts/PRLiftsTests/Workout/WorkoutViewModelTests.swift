import XCTest
import SwiftData
import PRLiftsCore
@testable import PRLifts

@MainActor
final class WorkoutViewModelTests: XCTestCase {
    private var container: ModelContainer!
    private var context: ModelContext!
    private var workout: Workout!
    private var sut: WorkoutViewModel!

    override func setUp() async throws {
        container = try PRLiftsSchema.makeContainer(inMemory: true)
        context = container.mainContext
        workout = Workout(type: .adHoc, format: .weightlifting)
        context.insert(workout)
        try context.save()
        sut = WorkoutViewModel(workout: workout)
    }

    override func tearDown() async throws {
        sut = nil
        workout = nil
        context = nil
        container = nil
    }

    // MARK: Helpers

    /// Adds one exercise to the workout and returns the resulting WorkoutExercise.
    @discardableResult
    private func addWorkoutExercise() -> WorkoutExercise {
        let exercise = Exercise(
            name: "Squat",
            category: .strength,
            muscleGroup: .quads,
            equipment: .barbell
        )
        context.insert(exercise)
        sut.addExercise(exercise) { self.context.insert($0) }
        return sut.sortedExercises.first!
    }

    // MARK: Initial state

    func testInitial_phaseIsActive() {
        XCTAssertEqual(sut.phase, .active)
    }

    func testInitial_elapsedSecondsIsZero() {
        XCTAssertEqual(sut.elapsedSeconds, 0)
    }

    func testInitial_totalSetCountIsZero() {
        XCTAssertEqual(sut.totalSetCount, 0)
    }

    // MARK: addExercise

    func testAddExercise_appendsToWorkout() {
        let we = addWorkoutExercise()
        XCTAssertEqual(sut.sortedExercises.count, 1)
        XCTAssertEqual(sut.sortedExercises.first?.id, we.id)
    }

    func testAddExercise_initializesFormState() {
        let we = addWorkoutExercise()
        XCTAssertEqual(sut.weightInputs[we.id], "")
        XCTAssertEqual(sut.repsInputs[we.id], "")
    }

    // MARK: logSet

    func testLogSet_withValidInput_returnsTrue() {
        let we = addWorkoutExercise()
        sut.weightInputs[we.id] = "100"
        sut.repsInputs[we.id] = "5"
        let result = sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        XCTAssertTrue(result)
    }

    func testLogSet_withEmptyReps_returnsFalse() {
        let we = addWorkoutExercise()
        sut.weightInputs[we.id] = "100"
        sut.repsInputs[we.id] = ""
        let result = sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        XCTAssertFalse(result)
    }

    func testLogSet_withZeroReps_returnsFalse() {
        let we = addWorkoutExercise()
        sut.repsInputs[we.id] = "0"
        let result = sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        XCTAssertFalse(result)
    }

    func testLogSet_withNonNumericReps_returnsFalse() {
        let we = addWorkoutExercise()
        sut.repsInputs[we.id] = "abc"
        let result = sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        XCTAssertFalse(result)
    }

    func testLogSet_appendsToWorkoutExercise() {
        let we = addWorkoutExercise()
        sut.repsInputs[we.id] = "8"
        sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        XCTAssertEqual(we.sets.count, 1)
    }

    func testLogSet_incrementsSetNumber() {
        let we = addWorkoutExercise()
        sut.repsInputs[we.id] = "8"
        sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        sut.repsInputs[we.id] = "8"
        sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        let sorted = we.sets.sorted { $0.setNumber < $1.setNumber }
        XCTAssertEqual(sorted[0].setNumber, 1)
        XCTAssertEqual(sorted[1].setNumber, 2)
    }

    func testLogSet_callsInsertClosure() {
        let we = addWorkoutExercise()
        sut.repsInputs[we.id] = "5"
        var inserted: [WorkoutSet] = []
        sut.logSet(for: we, weightUnit: .lbs) { inserted.append($0) }
        XCTAssertEqual(inserted.count, 1)
    }

    func testLogSet_clearsInputsAfterSuccess() {
        let we = addWorkoutExercise()
        sut.weightInputs[we.id] = "80"
        sut.repsInputs[we.id] = "10"
        sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        XCTAssertEqual(sut.weightInputs[we.id], "")
        XCTAssertEqual(sut.repsInputs[we.id], "")
    }

    func testLogSet_setsConfirmationExerciseID() {
        let we = addWorkoutExercise()
        sut.repsInputs[we.id] = "5"
        sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        XCTAssertEqual(sut.setConfirmationExerciseID, we.id)
    }

    func testLogSet_storesWeightAndUnit() {
        let we = addWorkoutExercise()
        sut.weightInputs[we.id] = "60"
        sut.repsInputs[we.id] = "12"
        sut.logSet(for: we, weightUnit: .kg) { context.insert($0) }
        let set = we.sets.first!
        XCTAssertEqual(set.weight, 60)
        XCTAssertEqual(set.weightUnit, .kg)
    }

    func testLogSet_nilWeightUnit_whenNoWeight() {
        let we = addWorkoutExercise()
        sut.weightInputs[we.id] = ""
        sut.repsInputs[we.id] = "10"
        sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        XCTAssertNil(we.sets.first?.weightUnit)
    }

    func testLogSet_incrementsTotalSetCount() {
        let we = addWorkoutExercise()
        sut.repsInputs[we.id] = "5"
        sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        XCTAssertEqual(sut.totalSetCount, 1)
    }

    // MARK: requestFinish / confirmFinish

    func testRequestFinish_withNoSets_showsEmptyAlert() {
        sut.requestFinish()
        XCTAssertTrue(sut.isShowingEmptyWorkoutAlert)
    }

    func testRequestFinish_withSets_transitionsToSynced() {
        let we = addWorkoutExercise()
        sut.repsInputs[we.id] = "5"
        sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        sut.requestFinish()
        XCTAssertEqual(sut.phase, .synced)
    }

    func testConfirmFinish_setsStatusCompleted() {
        sut.confirmFinish()
        XCTAssertEqual(workout.status, .completed)
    }

    func testConfirmFinish_setsDurationSeconds() {
        sut.confirmFinish()
        XCTAssertNotNil(workout.durationSeconds)
        XCTAssertGreaterThan(workout.durationSeconds ?? 0, 0)
    }

    func testConfirmFinish_setsCompletedAt() {
        sut.confirmFinish()
        XCTAssertNotNil(workout.completedAt)
    }

    func testConfirmFinish_transitionsToSynced() {
        sut.confirmFinish()
        XCTAssertEqual(sut.phase, .synced)
    }

    // MARK: requestCancel / discard

    func testRequestCancel_withNoSets_transitionsToSynced() {
        sut.requestCancel()
        XCTAssertEqual(sut.phase, .synced)
    }

    func testRequestCancel_withSets_showsCancelAlert() {
        let we = addWorkoutExercise()
        sut.repsInputs[we.id] = "5"
        sut.logSet(for: we, weightUnit: .lbs) { context.insert($0) }
        sut.requestCancel()
        XCTAssertTrue(sut.isShowingCancelAlert)
    }

    func testDiscard_callsDeleteClosure() {
        var deleted: [Workout] = []
        sut.discard { deleted.append($0) }
        XCTAssertEqual(deleted.count, 1)
        XCTAssertEqual(deleted.first?.id, workout.id)
    }

    func testDiscard_transitionsToSynced() {
        sut.discard { _ in }
        XCTAssertEqual(sut.phase, .synced)
    }

    // MARK: formattedElapsed

    func testFormattedElapsed_underOneHour() {
        sut.elapsedSeconds = 125
        XCTAssertEqual(sut.formattedElapsed, "02:05")
    }

    func testFormattedElapsed_overOneHour() {
        sut.elapsedSeconds = 3661
        XCTAssertEqual(sut.formattedElapsed, "1:01:01")
    }

    func testFormattedElapsed_zero() {
        XCTAssertEqual(sut.formattedElapsed, "00:00")
    }
}
