import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class UserModelTests: XCTestCase {
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
        let user = User.stub()
        context.insert(user)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.unitPreference, .lbs)
        XCTAssertEqual(result.measurementUnit, .cm)
        XCTAssertEqual(result.gender, .na)
        XCTAssertEqual(result.betaTier, .none)
        XCTAssertNil(result.goal)
        XCTAssertNil(result.phase2CompletedAt)
        XCTAssertNil(result.dateOfBirth)
    }

    func testPersistsEmail() throws {
        let user = User.stub(email: "athlete@example.com", displayName: "Jordan")
        context.insert(user)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.email, "athlete@example.com")
        XCTAssertEqual(result.displayName, "Jordan")
    }

    func testNullableEmailAllowed() throws {
        let user = User.stub(email: nil, displayName: nil)
        context.insert(user)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertNil(result.email)
        XCTAssertNil(result.displayName)
    }

    func testGoalEnum() throws {
        let user = User.stub(goal: .buildMuscle)
        context.insert(user)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.goal, .buildMuscle)
    }

    func testBetaTierEnum() throws {
        let user = User.stub(betaTier: .fullAccess)
        context.insert(user)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.betaTier, .fullAccess)
    }

    func testUnitPreferenceEnum() throws {
        let user = User.stub(unitPreference: .kg)
        context.insert(user)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.unitPreference, .kg)
    }

    func testPhase2CompletedAtStoredAsUTC() throws {
        let now = Date()
        let user = User(phase2CompletedAt: now)
        context.insert(user)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(
            result.phase2CompletedAt?.timeIntervalSinceReferenceDate ?? 0,
            now.timeIntervalSinceReferenceDate,
            accuracy: 0.001
        )
    }

    func testIDIsPreservedAfterSave() throws {
        let id = UUID()
        let user = User.stub(id: id)
        context.insert(user)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.id, id)
    }

    func testEmptyRelationshipsOnCreation() throws {
        let user = User.stub()
        context.insert(user)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertTrue(result.workouts.isEmpty)
        XCTAssertTrue(result.personalRecords.isEmpty)
        XCTAssertTrue(result.jobs.isEmpty)
        XCTAssertTrue(result.syncEventLogs.isEmpty)
    }

    func testMultipleUsersCanExist() throws {
        context.insert(User.stub(id: UUID(), email: "a@example.com"))
        context.insert(User.stub(id: UUID(), email: "b@example.com"))
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<User>())
        XCTAssertEqual(fetched.count, 2)
    }
}
