import Foundation
import Network

public final class LiveNetworkPathMonitor: NetworkPathMonitorProtocol, @unchecked Sendable {
    private let inner = NWPathMonitor()

    public init() {}

    public func setHandler(_ handler: @escaping @Sendable (SyncPathStatus) -> Void) {
        inner.pathUpdateHandler = { path in
            let status: SyncPathStatus = path.status == .satisfied ? .satisfied : .unsatisfied
            handler(status)
        }
    }

    public func start(queue: DispatchQueue) {
        inner.start(queue: queue)
    }

    public func cancel() {
        inner.cancel()
    }
}
