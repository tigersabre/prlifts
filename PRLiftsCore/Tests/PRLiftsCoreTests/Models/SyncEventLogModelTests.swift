import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class SyncEventLogModelTests: XCTestCase {
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
        let entityID = UUID()
        let log = SyncEventLog.stub(
            eventType: .syncSuccess,
            entityType: .workout,
            entityID: entityID
        )
        context.insert(log)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.eventType, .syncSuccess)
        XCTAssertEqual(result.entityType, .workout)
        XCTAssertEqual(result.entityID, entityID)
    }

    func testAllEventTypes() throws {
        for eventType in SyncEventType.allCases {
            let log = SyncEventLog.stub(eventType: eventType, entityID: UUID())
            context.insert(log)
        }
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        XCTAssertEqual(fetched.count, SyncEventType.allCases.count)
    }

    func testAllEntityTypes() throws {
        for entityType in SyncEntityType.allCases {
            let log = SyncEventLog.stub(entityType: entityType, entityID: UUID())
            context.insert(log)
        }
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        XCTAssertEqual(fetched.count, SyncEntityType.allCases.count)
    }

    func testDetailPersistence() throws {
        let log = SyncEventLog.stub(detail: "Network timeout after 30s")
        context.insert(log)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        XCTAssertEqual(fetched.first?.detail, "Network timeout after 30s")
    }

    func testNilDetailAllowed() throws {
        let log = SyncEventLog.stub(detail: nil)
        context.insert(log)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        XCTAssertNil(fetched.first?.detail)
    }

    func testUploadedAtNilByDefault() throws {
        let log = SyncEventLog.stub()
        context.insert(log)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        XCTAssertNil(fetched.first?.uploadedAt)
    }

    func testUploadedAtPersistence() throws {
        let uploadTime = Date()
        let log = SyncEventLog.stub()
        log.uploadedAt = uploadTime
        context.insert(log)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        let result = try XCTUnwrap(fetched.first?.uploadedAt)

        XCTAssertEqual(
            result.timeIntervalSinceReferenceDate,
            uploadTime.timeIntervalSinceReferenceDate,
            accuracy: 0.001
        )
    }

    func testOccurredAtPersistence() throws {
        let occurredAt = Date().addingTimeInterval(-3600)
        let log = SyncEventLog.stub(occurredAt: occurredAt)
        context.insert(log)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(
            result.occurredAt.timeIntervalSinceReferenceDate,
            occurredAt.timeIntervalSinceReferenceDate,
            accuracy: 0.001
        )
    }

    func testSyncFailureWithDetail() throws {
        let log = SyncEventLog.stub(
            eventType: .syncFailure,
            entityType: .workoutSet,
            detail: "Connection refused"
        )
        context.insert(log)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.eventType, .syncFailure)
        XCTAssertEqual(result.detail, "Connection refused")
    }

    func testConflictResolvedEvent() throws {
        let log = SyncEventLog.stub(
            eventType: .conflictResolved,
            entityType: .personalRecord,
            detail: "Server timestamp wins"
        )
        context.insert(log)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        XCTAssertEqual(fetched.first?.eventType, .conflictResolved)
    }

    func testEntityIDPreserved() throws {
        let entityID = UUID()
        let log = SyncEventLog.stub(entityID: entityID)
        context.insert(log)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SyncEventLog>())
        XCTAssertEqual(fetched.first?.entityID, entityID)
    }
}
