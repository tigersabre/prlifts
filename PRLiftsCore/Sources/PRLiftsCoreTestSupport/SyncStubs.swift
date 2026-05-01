import Foundation
import PRLiftsCore

public final class MockSyncClient: SyncClientProtocol, @unchecked Sendable {
    public private(set) var uploadedEntities: [(SyncEntityType, UUID)] = []
    public var uploadError: Error?
    public private(set) var uploadCallCount = 0

    public init() {}

    public func upload(entityType: SyncEntityType, entityID: UUID) async throws {
        uploadCallCount += 1
        if let error = uploadError {
            throw error
        }
        uploadedEntities.append((entityType, entityID))
    }
}

public final class MockNetworkPathMonitor: NetworkPathMonitorProtocol, @unchecked Sendable {
    private var handler: (@Sendable (SyncPathStatus) -> Void)?
    public private(set) var isStarted = false
    public private(set) var isCancelled = false

    public init() {}

    public func setHandler(_ handler: @escaping @Sendable (SyncPathStatus) -> Void) {
        self.handler = handler
    }

    public func start(queue: DispatchQueue) {
        isStarted = true
    }

    public func cancel() {
        isCancelled = true
        isStarted = false
    }

    public func simulatePathChange(_ status: SyncPathStatus) {
        handler?(status)
    }
}
