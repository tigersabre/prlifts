import Foundation
import SwiftData

@MainActor
public final class SyncEngine: SyncEngineProtocol {
    private let container: ModelContainer
    private let client: any SyncClientProtocol
    private let monitor: any NetworkPathMonitorProtocol
    private let monitorQueue = DispatchQueue(label: "com.prlifts.syncengine.monitor", qos: .utility)

    public init(
        container: ModelContainer,
        client: any SyncClientProtocol,
        monitor: any NetworkPathMonitorProtocol = LiveNetworkPathMonitor()
    ) {
        self.container = container
        self.client = client
        self.monitor = monitor
    }

    public func start() {
        monitor.setHandler { [weak self] status in
            guard status == .satisfied else { return }
            Task { @MainActor [weak self] in
                await self?.syncPending(trigger: .connectivityRestored)
            }
        }
        monitor.start(queue: monitorQueue)
    }

    public func stop() {
        monitor.cancel()
    }

    public func handleAppForeground() async {
        await syncPending(trigger: .appForeground)
    }

    public func recoverFromForceQuit() async {
        await syncPending(trigger: .forceQuitRecovery)
    }

    private func syncPending(trigger: SyncTrigger) async {
        let context = container.mainContext
        let pending: [SyncEventLog]
        do {
            pending = try fetchPendingEntries(context: context)
        } catch {
            return
        }
        for entry in pending {
            await uploadEntry(entry, context: context)
        }
    }

    private func fetchPendingEntries(context: ModelContext) throws -> [SyncEventLog] {
        let descriptor = FetchDescriptor<SyncEventLog>(
            predicate: #Predicate { $0.uploadedAt == nil }
        )
        return try context.fetch(descriptor).filter { $0.eventType == .writeAttempt }
    }

    private func uploadEntry(_ entry: SyncEventLog, context: ModelContext) async {
        do {
            try await client.upload(entityType: entry.entityType, entityID: entry.entityID)
            entry.uploadedAt = Date()
            try context.save()
        } catch {
            let failure = SyncEventLog(
                eventType: .syncFailure,
                entityType: entry.entityType,
                entityID: entry.entityID,
                detail: error.localizedDescription
            )
            context.insert(failure)
            try? context.save()
        }
    }
}

private enum SyncTrigger {
    case appForeground
    case connectivityRestored
    case forceQuitRecovery
    case backgroundRefresh
}
