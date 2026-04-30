import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class WorkoutModelTests: XCTestCase {
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

    func testDefaultStatus() throws {
        let workout = Workout.stub()
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.status, .inProgress)
    }

    func testStatusTransitions() throws {
        let workout = Workout.stub(status: .completed)
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.status, .completed)
    }

    func testPartialCompletionStatus() throws {
        let workout = Workout.stub(status: .partialCompletion)
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertEqual(fetched.first?.status, .partialCompletion)
    }

    func testWorkoutTypePersistence() throws {
        let workout = Workout.stub(type: .planned)
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertEqual(fetched.first?.type, .planned)
    }

    func testWorkoutFormatPersistence() throws {
        let workout = Workout.stub(format: .cardio)
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertEqual(fetched.first?.format, .cardio)
    }

    func testOptionalLocationPersists() throws {
        let workout = Workout.stub(location: .outdoor)
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertEqual(fetched.first?.location, .outdoor)
    }

    func testNilLocationAllowed() throws {
        let workout = Workout(type: .adHoc, format: .weightlifting, location: nil)
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertNil(fetched.first?.location)
    }

    func testRatingPersistence() throws {
        let workout = Workout(type: .adHoc, format: .weightlifting)
        workout.rating = 4
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertEqual(fetched.first?.rating, 4)
    }

    func testDurationSecondsPersistence() throws {
        let workout = Workout(type: .adHoc, format: .mixed)
        workout.durationSeconds = 3600
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertEqual(fetched.first?.durationSeconds, 3600)
    }

    func testServerReceivedAtDefaults() throws {
        let before = Date()
        let workout = Workout.stub()
        let after = Date()

        XCTAssertGreaterThanOrEqual(workout.serverReceivedAt, before)
        XCTAssertLessThanOrEqual(workout.serverReceivedAt, after)
    }

    func testCompletedAtPersistence() throws {
        let completedAt = Date()
        let workout = Workout(type: .adHoc, format: .weightlifting, completedAt: completedAt)
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        let result = try XCTUnwrap(fetched.first?.completedAt)

        XCTAssertEqual(
            result.timeIntervalSinceReferenceDate,
            completedAt.timeIntervalSinceReferenceDate,
            accuracy: 0.001
        )
    }

    func testEmptyExercisesOnCreation() throws {
        let workout = Workout.stub()
        context.insert(workout)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Workout>())
        XCTAssertTrue(fetched.first?.exercises.isEmpty ?? false)
    }
}
