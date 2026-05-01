import Foundation
import SwiftData

@MainActor
public final class SyncQueue {
    private let context: ModelContext

    public init(context: ModelContext) {
        self.context = context
    }

    public func recordWriteAttempt(entityType: SyncEntityType, entityID: UUID) throws {
        let entry = SyncEventLog(
            eventType: .writeAttempt,
            entityType: entityType,
            entityID: entityID
        )
        context.insert(entry)
        try context.save()
    }
}
