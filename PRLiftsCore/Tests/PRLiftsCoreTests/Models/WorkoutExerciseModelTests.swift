import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class WorkoutExerciseModelTests: XCTestCase {
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

    func testOrderIndexPersistence() throws {
        let workoutExercise = WorkoutExercise.stub(orderIndex: 3)
        context.insert(workoutExercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutExercise>())
        XCTAssertEqual(fetched.first?.orderIndex, 3)
    }

    func testOptionalNotesPersistence() throws {
        let workoutExercise = WorkoutExercise(orderIndex: 0, notes: "Focus on form")
        context.insert(workoutExercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutExercise>())
        XCTAssertEqual(fetched.first?.notes, "Focus on form")
    }

    func testNilNotesAllowed() throws {
        let workoutExercise = WorkoutExercise.stub()
        context.insert(workoutExercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutExercise>())
        XCTAssertNil(fetched.first?.notes)
    }

    func testRestSecondsPersistence() throws {
        let workoutExercise = WorkoutExercise.stub(restSeconds: 120)
        context.insert(workoutExercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutExercise>())
        XCTAssertEqual(fetched.first?.restSeconds, 120)
    }

    func testNilRestSecondsAllowed() throws {
        let workoutExercise = WorkoutExercise(orderIndex: 0, restSeconds: nil)
        context.insert(workoutExercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutExercise>())
        XCTAssertNil(fetched.first?.restSeconds)
    }

    func testIDPreserved() throws {
        let id = UUID()
        let workoutExercise = WorkoutExercise.stub(id: id)
        context.insert(workoutExercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutExercise>())
        XCTAssertEqual(fetched.first?.id, id)
    }

    func testEmptySetsOnCreation() throws {
        let workoutExercise = WorkoutExercise.stub()
        context.insert(workoutExercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutExercise>())
        XCTAssertTrue(fetched.first?.sets.isEmpty ?? false)
    }

    func testTimestampsDefault() throws {
        let before = Date()
        let workoutExercise = WorkoutExercise.stub()
        let after = Date()

        XCTAssertGreaterThanOrEqual(workoutExercise.createdAt, before)
        XCTAssertLessThanOrEqual(workoutExercise.createdAt, after)
        XCTAssertGreaterThanOrEqual(workoutExercise.updatedAt, before)
        XCTAssertLessThanOrEqual(workoutExercise.updatedAt, after)
    }
}
