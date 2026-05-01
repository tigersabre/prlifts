import Foundation

public enum SyncPathStatus: Sendable, Equatable {
    case satisfied
    case unsatisfied
}

public protocol NetworkPathMonitorProtocol: AnyObject, Sendable {
    func setHandler(_ handler: @escaping @Sendable (SyncPathStatus) -> Void)
    func start(queue: DispatchQueue)
    func cancel()
}
