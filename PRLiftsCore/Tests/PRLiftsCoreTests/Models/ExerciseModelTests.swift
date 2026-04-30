import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class ExerciseModelTests: XCTestCase {
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

    func testBasicPersistence() throws {
        let exercise = Exercise.stub()
        context.insert(exercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Exercise>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.name, "Bench Press")
        XCTAssertEqual(result.category, .strength)
        XCTAssertEqual(result.muscleGroup, .midChest)
        XCTAssertEqual(result.equipment, .barbell)
        XCTAssertFalse(result.isCustom)
    }

    func testSecondaryMuscleGroupsArray() throws {
        let exercise = Exercise.stub(secondaryMuscleGroups: [.shoulders, .triceps, .biceps])
        context.insert(exercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Exercise>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.secondaryMuscleGroups.count, 3)
        XCTAssertTrue(result.secondaryMuscleGroups.contains(.shoulders))
        XCTAssertTrue(result.secondaryMuscleGroups.contains(.triceps))
        XCTAssertTrue(result.secondaryMuscleGroups.contains(.biceps))
    }

    func testEmptySecondaryMuscleGroups() throws {
        let exercise = Exercise.stub(secondaryMuscleGroups: [])
        context.insert(exercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Exercise>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertTrue(result.secondaryMuscleGroups.isEmpty)
    }

    func testOptionalFields() throws {
        let exercise = Exercise(
            name: "Pull-up",
            category: .strength,
            muscleGroup: .upperBack,
            equipment: .bodyweight,
            instructions: "Hang from bar and pull up",
            demoURL: "https://example.com/pullup.gif"
        )
        context.insert(exercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Exercise>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.instructions, "Hang from bar and pull up")
        XCTAssertEqual(result.demoURL, "https://example.com/pullup.gif")
    }

    func testNilOptionalFields() throws {
        let exercise = Exercise.stub()
        context.insert(exercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Exercise>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertNil(result.instructions)
        XCTAssertNil(result.demoURL)
        XCTAssertNil(result.createdBy)
    }

    func testCustomExercise() throws {
        let creatorID = UUID()
        let exercise = Exercise.stub(isCustom: true)
        exercise.createdBy = creatorID
        context.insert(exercise)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Exercise>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertTrue(result.isCustom)
        XCTAssertEqual(result.createdBy, creatorID)
    }

    func testAllCategoriesAreValid() {
        for category in ExerciseCategory.allCases {
            let exercise = Exercise(
                name: "Test \(category.rawValue)",
                category: category,
                muscleGroup: .abs,
                equipment: .bodyweight
            )
            XCTAssertEqual(exercise.category, category)
        }
    }

    func testAllEquipmentTypesAreValid() {
        for equipment in ExerciseEquipment.allCases {
            let exercise = Exercise(
                name: "Test \(equipment.rawValue)",
                category: .strength,
                muscleGroup: .abs,
                equipment: equipment
            )
            XCTAssertEqual(exercise.equipment, equipment)
        }
    }

    func testAllMuscleGroupsAreValid() {
        for group in MuscleGroup.allCases {
            let exercise = Exercise(
                name: "Test \(group.rawValue)",
                category: .strength,
                muscleGroup: group,
                equipment: .bodyweight
            )
            XCTAssertEqual(exercise.muscleGroup, group)
        }
    }
}
