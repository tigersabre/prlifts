import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class PersonalRecordModelTests: XCTestCase {
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
        let setID = UUID()
        let pr = PersonalRecord.stub(
            value: 315.0,
            valueUnit: .lbs,
            workoutSetID: setID
        )
        context.insert(pr)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<PersonalRecord>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.value, 315.0, accuracy: 0.001)
        XCTAssertEqual(result.valueUnit, .lbs)
        XCTAssertEqual(result.workoutSetID, setID)
    }

    func testRecordTypePersistence() throws {
        for recordType in RecordType.allCases {
            let pr = PersonalRecord(
                weightModifier: .none,
                recordType: recordType,
                value: 100.0,
                recordedAt: Date(),
                workoutSetID: UUID()
            )
            context.insert(pr)
        }
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<PersonalRecord>())
        XCTAssertEqual(fetched.count, RecordType.allCases.count)
    }

    func testWeightModifierPersistence() throws {
        let pr = PersonalRecord.stub(weightModifier: .assisted)
        context.insert(pr)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<PersonalRecord>())
        XCTAssertEqual(fetched.first?.weightModifier, .assisted)
    }

    func testPreviousValuePersistence() throws {
        let previousDate = Date().addingTimeInterval(-86400)
        let pr = PersonalRecord.stub(
            value: 225.0,
            previousValue: 205.0,
            workoutSetID: UUID()
        )
        pr.previousRecordedAt = previousDate
        context.insert(pr)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<PersonalRecord>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(try XCTUnwrap(result.previousValue), 205.0, accuracy: 0.001)
        XCTAssertNotNil(result.previousRecordedAt)
    }

    func testNilPreviousValueAllowed() throws {
        let pr = PersonalRecord(
            weightModifier: .none,
            recordType: .heaviestWeight,
            value: 135.0,
            recordedAt: Date(),
            workoutSetID: UUID()
        )
        context.insert(pr)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<PersonalRecord>())
        XCTAssertNil(fetched.first?.previousValue)
        XCTAssertNil(fetched.first?.previousRecordedAt)
    }

    func testWorkoutSetIDStoredAsUUID() throws {
        let setID = UUID()
        let pr = PersonalRecord.stub(workoutSetID: setID)
        context.insert(pr)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<PersonalRecord>())
        XCTAssertEqual(fetched.first?.workoutSetID, setID)
    }

    func testValueUnitNilAllowed() throws {
        let pr = PersonalRecord(
            weightModifier: .none,
            recordType: .mostReps,
            value: 25.0,
            valueUnit: nil,
            recordedAt: Date(),
            workoutSetID: UUID()
        )
        context.insert(pr)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<PersonalRecord>())
        XCTAssertNil(fetched.first?.valueUnit)
    }

    func testAllValueUnits() {
        for unit in ValueUnit.allCases {
            let pr = PersonalRecord(
                weightModifier: .none,
                recordType: .longestDistance,
                value: 100.0,
                valueUnit: unit,
                recordedAt: Date(),
                workoutSetID: UUID()
            )
            XCTAssertEqual(pr.valueUnit, unit)
        }
    }

    func testWeightedAndBodyweightPRsAreDistinct() throws {
        let exerciseID = UUID()
        let setID1 = UUID()
        let setID2 = UUID()

        let weightedPR = PersonalRecord(
            weightModifier: .weighted,
            recordType: .heaviestWeight,
            value: 225.0,
            valueUnit: .lbs,
            recordedAt: Date(),
            workoutSetID: setID1
        )
        let bodyweightPR = PersonalRecord(
            weightModifier: .none,
            recordType: .heaviestWeight,
            value: 185.0,
            valueUnit: .lbs,
            recordedAt: Date(),
            workoutSetID: setID2
        )

        context.insert(weightedPR)
        context.insert(bodyweightPR)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<PersonalRecord>())
        XCTAssertEqual(fetched.count, 2)

        let weighted = fetched.first { $0.weightModifier == .weighted }
        let bodyweight = fetched.first { $0.weightModifier == .none }

        XCTAssertNotNil(weighted)
        XCTAssertNotNil(bodyweight)
        XCTAssertEqual(try XCTUnwrap(weighted).value, 225.0, accuracy: 0.001)
        XCTAssertEqual(try XCTUnwrap(bodyweight).value, 185.0, accuracy: 0.001)
        _ = exerciseID  // exerciseID would be set via the exercise relationship
    }
}
