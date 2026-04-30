import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class WorkoutSetModelTests: XCTestCase {
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

    func testDefaultValues() throws {
        let workoutSet = WorkoutSet(setNumber: 1, reps: 10)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.setType, .normal)
        XCTAssertEqual(result.weightModifier, .none)
        XCTAssertFalse(result.isCompleted)
    }

    func testWeightAndRepsPersistence() throws {
        let workoutSet = WorkoutSet.stub(weight: 135.0, weightUnit: .lbs, reps: 8)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(try XCTUnwrap(result.weight), 135.0, accuracy: 0.001)
        XCTAssertEqual(result.weightUnit, .lbs)
        XCTAssertEqual(result.reps, 8)
    }

    func testKilogramWeightUnit() throws {
        let workoutSet = WorkoutSet.stub(weight: 60.0, weightUnit: .kg, reps: 10)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertEqual(fetched.first?.weightUnit, .kg)
    }

    func testSetTypePersistence() throws {
        let workoutSet = WorkoutSet.stub(setType: .warmup)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertEqual(fetched.first?.setType, .warmup)
    }

    func testWeightModifierAssisted() throws {
        let workoutSet = WorkoutSet(
            setNumber: 1,
            weightModifier: .assisted,
            modifierValue: 45.0,
            modifierUnit: .lbs,
            reps: 10
        )
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.weightModifier, .assisted)
        XCTAssertEqual(try XCTUnwrap(result.modifierValue), 45.0, accuracy: 0.001)
        XCTAssertEqual(result.modifierUnit, .lbs)
    }

    func testWeightModifierWeighted() throws {
        let workoutSet = WorkoutSet(
            setNumber: 1,
            weightModifier: .weighted,
            modifierValue: 25.0,
            modifierUnit: .lbs,
            reps: 12
        )
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertEqual(fetched.first?.weightModifier, .weighted)
    }

    func testDurationSecondsPersistence() throws {
        let workoutSet = WorkoutSet(setNumber: 1, durationSeconds: 60)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertEqual(fetched.first?.durationSeconds, 60)
    }

    func testDistanceMetersPersistence() throws {
        let workoutSet = WorkoutSet(setNumber: 1, distanceMeters: 400.0)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertEqual(try XCTUnwrap(fetched.first?.distanceMeters), 400.0, accuracy: 0.001)
    }

    func testRPEPersistence() throws {
        let workoutSet = WorkoutSet(setNumber: 1, weight: 200.0, reps: 5, rpe: 9)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertEqual(fetched.first?.rpe, 9)
    }

    func testCaloriesPersistence() throws {
        let workoutSet = WorkoutSet(setNumber: 1, durationSeconds: 1800, calories: 320)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertEqual(fetched.first?.calories, 320)
    }

    func testIsCompletedPersistence() throws {
        let workoutSet = WorkoutSet.stub(isCompleted: true)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertTrue(fetched.first?.isCompleted ?? false)
    }

    func testPRSetTypePersistence() throws {
        let workoutSet = WorkoutSet.stub(setType: .pr)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertEqual(fetched.first?.setType, .pr)
    }

    func testSetNumberPersistence() throws {
        let workoutSet = WorkoutSet.stub(setNumber: 5)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertEqual(fetched.first?.setNumber, 5)
    }

    func testNilWeightAllowed() throws {
        let workoutSet = WorkoutSet(setNumber: 1, durationSeconds: 30)
        context.insert(workoutSet)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<WorkoutSet>())
        XCTAssertNil(fetched.first?.weight)
        XCTAssertNil(fetched.first?.weightUnit)
    }
}
