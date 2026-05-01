import Foundation

@MainActor
public protocol SyncEngineProtocol: AnyObject {
    func start()
    func stop()
    func handleAppForeground() async
    func recoverFromForceQuit() async
}
