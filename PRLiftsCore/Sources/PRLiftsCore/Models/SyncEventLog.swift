import Foundation
import SwiftData

@Model
public final class SyncEventLog {
    public var id: UUID
    public var eventType: SyncEventType
    public var entityType: SyncEntityType
    public var entityID: UUID
    public var detail: String?
    public var occurredAt: Date
    public var uploadedAt: Date?

    public var user: User?

    public init(
        id: UUID = UUID(),
        eventType: SyncEventType,
        entityType: SyncEntityType,
        entityID: UUID,
        detail: String? = nil,
        occurredAt: Date = Date(),
        uploadedAt: Date? = nil
    ) {
        self.id = id
        self.eventType = eventType
        self.entityType = entityType
        self.entityID = entityID
        self.detail = detail
        self.occurredAt = occurredAt
        self.uploadedAt = uploadedAt
    }
}
