import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class SyncEngineTests: XCTestCase {
    var container: ModelContainer!
    var context: ModelContext!
    var mockClient: MockSyncClient!
    var mockMonitor: MockNetworkPathMonitor!
    var engine: SyncEngine!

    override func setUp() async throws {
        container = try TestContainerFactory.make()
        context = container.mainContext
        mockClient = MockSyncClient()
        mockMonitor = MockNetworkPathMonitor()
        engine = SyncEngine(container: container, client: mockClient, monitor: mockMonitor)
    }

    override func tearDown() async throws {
        engine = nil
        mockMonitor = nil
        mockClient = nil
        context = nil
        container = nil
    }

    // MARK: - SyncQueue

    func testSyncQueueRecordsWriteAttemptWithNilUploadedAt() throws {
        let queue = SyncQueue(context: context)
        let entityID = UUID()

        try queue.recordWriteAttempt(entityType: .workoutSet, entityID: entityID)

        let entries = try context.fetch(FetchDescriptor<SyncEventLog>())
        let entry = try XCTUnwrap(entries.first)
        XCTAssertEqual(entry.eventType, .writeAttempt)
        XCTAssertEqual(entry.entityType, .workoutSet)
        XCTAssertEqual(entry.entityID, entityID)
        XCTAssertNil(entry.uploadedAt)
    }

    func testSyncQueueRecordsAllEntityTypes() throws {
        let queue = SyncQueue(context: context)

        for entityType in SyncEntityType.allCases {
            try queue.recordWriteAttempt(entityType: entityType, entityID: UUID())
        }

        let entries = try context.fetch(FetchDescriptor<SyncEventLog>())
        XCTAssertEqual(entries.count, SyncEntityType.allCases.count)
        XCTAssertTrue(entries.allSatisfy { $0.eventType == .writeAttempt })
        XCTAssertTrue(entries.allSatisfy { $0.uploadedAt == nil })
    }

    // MARK: - App Foreground Trigger

    func testAppForegroundSyncsAllPendingEntries() async throws {
        let entityID1 = UUID()
        let entityID2 = UUID()
        insertPendingEntry(entityType: .workout, entityID: entityID1)
        insertPendingEntry(entityType: .workoutSet, entityID: entityID2)
        try context.save()

        await engine.handleAppForeground()

        XCTAssertEqual(mockClient.uploadCallCount, 2)
        XCTAssertTrue(mockClient.uploadedEntities.contains { $0.1 == entityID1 })
        XCTAssertTrue(mockClient.uploadedEntities.contains { $0.1 == entityID2 })
    }

    func testAppForegroundSetsUploadedAtOnSuccess() async throws {
        let entry = insertPendingEntry(entityType: .workout, entityID: UUID())
        try context.save()

        await engine.handleAppForeground()

        XCTAssertNotNil(entry.uploadedAt)
    }

    func testAppForegroundNoOpWhenNoPendingEntries() async throws {
        await engine.handleAppForeground()

        XCTAssertEqual(mockClient.uploadCallCount, 0)
    }

    func testAppForegroundSkipsAlreadySyncedEntries() async throws {
        let synced = insertPendingEntry(entityType: .workout, entityID: UUID())
        synced.uploadedAt = Date()
        let pending = insertPendingEntry(entityType: .workoutSet, entityID: UUID())
        try context.save()

        await engine.handleAppForeground()

        XCTAssertEqual(mockClient.uploadCallCount, 1)
        XCTAssertNotNil(pending.uploadedAt)
        XCTAssertNotNil(synced.uploadedAt)
    }

    func testAppForegroundSkipsNonWriteAttemptEntries() async throws {
        let auditEntry = SyncEventLog(
            eventType: .syncFailure,
            entityType: .workout,
            entityID: UUID()
        )
        context.insert(auditEntry)
        try context.save()

        await engine.handleAppForeground()

        XCTAssertEqual(mockClient.uploadCallCount, 0)
    }

    // MARK: - Force-Quit Recovery

    func testRecoverFromForceQuitSyncsPreviousSessionData() async throws {
        let entityID = UUID()
        insertPendingEntry(entityType: .workout, entityID: entityID)
        try context.save()

        await engine.recoverFromForceQuit()

        XCTAssertEqual(mockClient.uploadCallCount, 1)
        XCTAssertEqual(mockClient.uploadedEntities.first?.1, entityID)
    }

    func testRecoverFromForceQuitMarksEntriesUploaded() async throws {
        let entry = insertPendingEntry(entityType: .workoutSet, entityID: UUID())
        try context.save()

        await engine.recoverFromForceQuit()

        XCTAssertNotNil(entry.uploadedAt)
    }

    func testRecoverFromForceQuitNoOpWhenAllSynced() async throws {
        let entry = insertPendingEntry(entityType: .workout, entityID: UUID())
        entry.uploadedAt = Date()
        try context.save()

        await engine.recoverFromForceQuit()

        XCTAssertEqual(mockClient.uploadCallCount, 0)
    }

    // MARK: - Connectivity Restored (NWPathMonitor)

    func testStartSetsHandlerAndStartsMonitor() {
        engine.start()

        XCTAssertTrue(mockMonitor.isStarted)
    }

    func testStopCancelsMonitor() {
        engine.start()
        engine.stop()

        XCTAssertTrue(mockMonitor.isCancelled)
        XCTAssertFalse(mockMonitor.isStarted)
    }

    func testConnectivityRestoredTriggersSyncPending() async throws {
        let entityID = UUID()
        insertPendingEntry(entityType: .workoutSet, entityID: entityID)
        try context.save()

        engine.start()
        mockMonitor.simulatePathChange(.satisfied)

        // The handler spawns Task { @MainActor in } which has multiple internal
        // suspension points (syncPending → uploadEntry → client.upload). Yield
        // multiple times so each step gets a chance to run on the main executor.
        for _ in 0..<10 {
            await Task.yield()
        }

        XCTAssertEqual(mockClient.uploadCallCount, 1)
        XCTAssertEqual(mockClient.uploadedEntities.first?.1, entityID)
    }

    func testUnsatisfiedPathDoesNotTriggerSync() async throws {
        insertPendingEntry(entityType: .workout, entityID: UUID())
        try context.save()

        engine.start()
        mockMonitor.simulatePathChange(.unsatisfied)

        await Task.yield()

        XCTAssertEqual(mockClient.uploadCallCount, 0)
    }

    // MARK: - Upload Failure Handling

    func testUploadFailureLeavesEntryPending() async throws {
        mockClient.uploadError = URLError(.notConnectedToInternet)
        let entry = insertPendingEntry(entityType: .workout, entityID: UUID())
        try context.save()

        await engine.handleAppForeground()

        XCTAssertNil(entry.uploadedAt)
    }

    func testUploadFailureCreatesFailureLogEntry() async throws {
        mockClient.uploadError = URLError(.notConnectedToInternet)
        insertPendingEntry(entityType: .workout, entityID: UUID())
        try context.save()

        await engine.handleAppForeground()

        let allEntries = try context.fetch(FetchDescriptor<SyncEventLog>())
        let failures = allEntries.filter { $0.eventType == .syncFailure }
        XCTAssertEqual(failures.count, 1)
    }

    func testUploadFailureEntryIsRetriedOnNextSync() async throws {
        mockClient.uploadError = URLError(.notConnectedToInternet)
        let entry = insertPendingEntry(entityType: .workout, entityID: UUID())
        try context.save()

        await engine.handleAppForeground()
        XCTAssertNil(entry.uploadedAt)

        mockClient.uploadError = nil
        await engine.handleAppForeground()

        XCTAssertNotNil(entry.uploadedAt)
        XCTAssertEqual(mockClient.uploadCallCount, 2)
    }

    // MARK: - Idempotency

    func testIdempotentSyncDoesNotUploadSameEntryTwice() async throws {
        insertPendingEntry(entityType: .workout, entityID: UUID())
        try context.save()

        await engine.handleAppForeground()
        await engine.handleAppForeground()

        XCTAssertEqual(mockClient.uploadCallCount, 1)
    }

    func testMultiplePendingEntriesAllUploaded() async throws {
        let ids = (0..<5).map { _ in UUID() }
        for id in ids {
            insertPendingEntry(entityType: .workoutSet, entityID: id)
        }
        try context.save()

        await engine.handleAppForeground()

        XCTAssertEqual(mockClient.uploadCallCount, 5)
        for id in ids {
            XCTAssertTrue(mockClient.uploadedEntities.contains { $0.1 == id })
        }
    }

    // MARK: - Helpers

    @discardableResult
    private func insertPendingEntry(entityType: SyncEntityType, entityID: UUID) -> SyncEventLog {
        let entry = SyncEventLog(
            eventType: .writeAttempt,
            entityType: entityType,
            entityID: entityID
        )
        context.insert(entry)
        return entry
    }
}
