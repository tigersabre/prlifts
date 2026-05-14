import Foundation

protocol WorkoutSyncServiceProtocol: Sendable {
    func fetchPRFlags(for workoutID: UUID) async throws -> [UUID: Bool]
}

final class StubWorkoutSyncService: WorkoutSyncServiceProtocol {
    nonisolated init() {}

    func fetchPRFlags(for workoutID: UUID) async throws -> [UUID: Bool] {
        // Use a longer delay in UI testing so XCUITest can reliably observe the loading state
        let delay: Duration = ProcessInfo.processInfo.arguments.contains("UITesting")
            ? .seconds(4)
            : .milliseconds(800)
        try await Task.sleep(for: delay)
        return [:]
    }
}
