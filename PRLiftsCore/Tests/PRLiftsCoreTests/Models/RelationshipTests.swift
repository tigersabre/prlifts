import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class RelationshipTests: XCTestCase {
    var container: ModelContainer!
    var context: ModelContext!

    override func setUp() async throws {
        container = try TestContainerFactory.make()
        context = container.mainContext
    }

    override func tearDown() async throws {
        context = nil
        container = nil
    }

    // MARK: - User ↔ Workout

    func testUserWorkoutRelationship() throws {
        let user = User.stub()
        let workout = Workout.stub()
        context.insert(user)
        context.insert(workout)
        user.workouts.append(workout)
        try context.save()

        let fetchedUsers = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetchedUsers.first)

        XCTAssertEqual(result.workouts.count, 1)
        XCTAssertEqual(result.workouts.first?.name, "Morning Session")
    }

    func testUserInverseOnWorkout() throws {
        let user = User.stub()
        let workout = Workout.stub()
        context.insert(user)
        context.insert(workout)
        user.workouts.append(workout)
        try context.save()

        let fetchedWorkouts = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertNotNil(fetchedWorkouts.first?.user)
    }

    func testUserCascadeDeletesWorkouts() throws {
        let user = User.stub()
        let workout = Workout.stub()
        context.insert(user)
        context.insert(workout)
        user.workouts.append(workout)
        try context.save()

        context.delete(user)
        try context.save()

        let workouts = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertTrue(workouts.isEmpty)
    }

    func testUserCanHaveMultipleWorkouts() throws {
        let user = User.stub()
        let workout1 = Workout.stub(id: UUID(), name: "Monday Push")
        let workout2 = Workout.stub(id: UUID(), name: "Tuesday Pull")
        let workout3 = Workout.stub(id: UUID(), name: "Thursday Legs")

        context.insert(user)
        context.insert(workout1)
        context.insert(workout2)
        context.insert(workout3)
        user.workouts.append(contentsOf: [workout1, workout2, workout3])
        try context.save()

        let fetchedUsers = try context.fetch(FetchDescriptor<User>())
        XCTAssertEqual(fetchedUsers.first?.workouts.count, 3)
    }

    // MARK: - Workout ↔ WorkoutExercise

    func testWorkoutExerciseRelationship() throws {
        let user = User.stub()
        let workout = Workout.stub()
        let exercise = Exercise.stub()
        let workoutExercise = WorkoutExercise.stub(orderIndex: 0)

        context.insert(user)
        context.insert(workout)
        context.insert(exercise)
        context.insert(workoutExercise)

        user.workouts.append(workout)
        workoutExercise.exercise = exercise
        workout.exercises.append(workoutExercise)
        try context.save()

        let fetchedWorkouts = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertEqual(fetchedWorkouts.first?.exercises.count, 1)
        XCTAssertEqual(fetchedWorkouts.first?.exercises.first?.orderIndex, 0)
    }

    func testWorkoutCascadeDeletesWorkoutExercises() throws {
        let user = User.stub()
        let workout = Workout.stub()
        let workoutExercise = WorkoutExercise.stub()

        context.insert(user)
        context.insert(workout)
        context.insert(workoutExercise)
        user.workouts.append(workout)
        workout.exercises.append(workoutExercise)
        try context.save()

        context.delete(workout)
        try context.save()

        let workoutExercises = try context.fetch(FetchDescriptor<WorkoutExercise>())
        XCTAssertTrue(workoutExercises.isEmpty)
    }

    // MARK: - WorkoutExercise ↔ WorkoutSet

    func testWorkoutSetRelationship() throws {
        let workoutExercise = WorkoutExercise.stub()
        let set1 = WorkoutSet.stub(setNumber: 1, weight: 135.0, reps: 10)
        let set2 = WorkoutSet.stub(setNumber: 2, weight: 145.0, reps: 8)

        context.insert(workoutExercise)
        context.insert(set1)
        context.insert(set2)
        workoutExercise.sets.append(contentsOf: [set1, set2])
        try context.save()

        let fetchedExercises = try context.fetch(FetchDescriptor<WorkoutExercise>())
        XCTAssertEqual(fetchedExercises.first?.sets.count, 2)
    }

    func testWorkoutExerciseCascadeDeletesSets() throws {
        let workoutExercise = WorkoutExercise.stub()
        let set = WorkoutSet.stub(setNumber: 1, reps: 10)

        context.insert(workoutExercise)
        context.insert(set)
        workoutExercise.sets.append(set)
        try context.save()

        context.delete(workoutExercise)
        try context.save()

        let sets = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertTrue(sets.isEmpty)
    }

    func testWorkoutSetInverseOnWorkoutExercise() throws {
        let workoutExercise = WorkoutExercise.stub()
        let workoutSet = WorkoutSet.stub(setNumber: 1, reps: 12)

        context.insert(workoutExercise)
        context.insert(workoutSet)
        workoutExercise.sets.append(workoutSet)
        try context.save()

        let fetchedSets = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertNotNil(fetchedSets.first?.workoutExercise)
    }

    // MARK: - User ↔ PersonalRecord

    func testUserPersonalRecordRelationship() throws {
        let user = User.stub()
        let pr = PersonalRecord.stub(value: 315.0, valueUnit: .lbs, workoutSetID: UUID())

        context.insert(user)
        context.insert(pr)
        user.personalRecords.append(pr)
        try context.save()

        let fetchedUsers = try context.fetch(FetchDescriptor<User>())
        XCTAssertEqual(fetchedUsers.first?.personalRecords.count, 1)
        XCTAssertEqual(try XCTUnwrap(fetchedUsers.first?.personalRecords.first?.value), 315.0, accuracy: 0.001)
    }

    func testUserCascadeDeletesPersonalRecords() throws {
        let user = User.stub()
        let pr = PersonalRecord.stub(workoutSetID: UUID())

        context.insert(user)
        context.insert(pr)
        user.personalRecords.append(pr)
        try context.save()

        context.delete(user)
        try context.save()

        let records = try context.fetch(FetchDescriptor<PersonalRecord>())
        XCTAssertTrue(records.isEmpty)
    }

    // MARK: - User ↔ Job

    func testUserJobRelationship() throws {
        let user = User.stub()
        let job = Job.stub(jobType: .insight)

        context.insert(user)
        context.insert(job)
        user.jobs.append(job)
        try context.save()

        let fetchedUsers = try context.fetch(FetchDescriptor<User>())
        XCTAssertEqual(fetchedUsers.first?.jobs.count, 1)
        XCTAssertEqual(fetchedUsers.first?.jobs.first?.jobType, .insight)
    }

    func testUserCascadeDeletesJobs() throws {
        let user = User.stub()
        let job = Job.stub()

        context.insert(user)
        context.insert(job)
        user.jobs.append(job)
        try context.save()

        context.delete(user)
        try context.save()

        let jobs = try context.fetch(FetchDescriptor<Job>())
        XCTAssertTrue(jobs.isEmpty)
    }

    // MARK: - User ↔ SyncEventLog

    func testUserSyncEventLogRelationship() throws {
        let user = User.stub()
        let log = SyncEventLog.stub(eventType: .writeAttempt, entityType: .workout)

        context.insert(user)
        context.insert(log)
        user.syncEventLogs.append(log)
        try context.save()

        let fetchedUsers = try context.fetch(FetchDescriptor<User>())
        XCTAssertEqual(fetchedUsers.first?.syncEventLogs.count, 1)
    }

    func testUserCascadeDeletesSyncEventLogs() throws {
        let user = User.stub()
        let log = SyncEventLog.stub()

        context.insert(user)
        context.insert(log)
        user.syncEventLogs.append(log)
        try context.save()

        context.delete(user)
        try context.save()

        let logs = try context.fetch(FetchDescriptor<SyncEventLog>())
        XCTAssertTrue(logs.isEmpty)
    }

    // MARK: - Exercise ↔ WorkoutExercise

    func testExerciseWorkoutExerciseRelationship() throws {
        let exercise = Exercise.stub()
        let workoutExercise = WorkoutExercise.stub()

        context.insert(exercise)
        context.insert(workoutExercise)
        workoutExercise.exercise = exercise
        try context.save()

        let fetchedExercise = try context.fetch(FetchDescriptor<Exercise>())
        XCTAssertEqual(fetchedExercise.first?.workoutExercises.count, 1)
    }

    // MARK: - Exercise ↔ PersonalRecord

    func testExercisePersonalRecordRelationship() throws {
        let exercise = Exercise.stub()
        let pr = PersonalRecord.stub(workoutSetID: UUID())

        context.insert(exercise)
        context.insert(pr)
        pr.exercise = exercise
        try context.save()

        let fetchedExercise = try context.fetch(FetchDescriptor<Exercise>())
        XCTAssertEqual(fetchedExercise.first?.personalRecords.count, 1)
    }

    // MARK: - Full chain

    func testFullWorkoutChain() throws {
        let user = User.stub()
        let exercise = Exercise.stub()
        let workout = Workout.stub()
        let workoutExercise = WorkoutExercise.stub(orderIndex: 0)
        let set1 = WorkoutSet.stub(setNumber: 1, weight: 225.0, reps: 5)
        let set2 = WorkoutSet.stub(setNumber: 2, weight: 235.0, reps: 3)

        context.insert(user)
        context.insert(exercise)
        context.insert(workout)
        context.insert(workoutExercise)
        context.insert(set1)
        context.insert(set2)

        user.workouts.append(workout)
        workoutExercise.exercise = exercise
        workout.exercises.append(workoutExercise)
        workoutExercise.sets.append(contentsOf: [set1, set2])
        try context.save()

        let fetchedUsers = try context.fetch(FetchDescriptor<User>())
        let fetchedUser = try XCTUnwrap(fetchedUsers.first)

        XCTAssertEqual(fetchedUser.workouts.count, 1)
        XCTAssertEqual(fetchedUser.workouts.first?.exercises.count, 1)
        XCTAssertEqual(fetchedUser.workouts.first?.exercises.first?.sets.count, 2)
        XCTAssertEqual(fetchedUser.workouts.first?.exercises.first?.exercise?.name, "Bench Press")
    }

    func testCascadeFromUserDeletesEntireChain() throws {
        let user = User.stub()
        let workout = Workout.stub()
        let workoutExercise = WorkoutExercise.stub()
        let workoutSet = WorkoutSet.stub(setNumber: 1, reps: 10)

        context.insert(user)
        context.insert(workout)
        context.insert(workoutExercise)
        context.insert(workoutSet)

        user.workouts.append(workout)
        workout.exercises.append(workoutExercise)
        workoutExercise.sets.append(workoutSet)
        try context.save()

        context.delete(user)
        try context.save()

        XCTAssertTrue(try context.fetch(FetchDescriptor<Workout>()).isEmpty)
        XCTAssertTrue(try context.fetch(FetchDescriptor<WorkoutExercise>()).isEmpty)
        XCTAssertTrue(try context.fetch(FetchDescriptor<WorkoutSet>()).isEmpty)
    }
}
