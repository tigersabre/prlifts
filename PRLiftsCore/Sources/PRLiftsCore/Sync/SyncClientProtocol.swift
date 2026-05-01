import Foundation

public protocol SyncClientProtocol: Sendable {
    func upload(entityType: SyncEntityType, entityID: UUID) async throws
}
