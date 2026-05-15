import Foundation

enum InsightServiceError: Error {
    case rateLimited
    case networkError
}

enum InsightPollStatus {
    case pending
    case processing
    case complete(String)
    case failed
    case expired
}

protocol InsightServiceProtocol: Sendable {
    /// POST /v1/jobs — returns job_id
    func requestInsight(workoutID: UUID) async throws -> UUID
    /// GET /v1/jobs/{job_id}
    func pollInsight(jobID: UUID) async throws -> InsightPollStatus
}

final class StubInsightService: InsightServiceProtocol {
    nonisolated init() {}

    func requestInsight(workoutID: UUID) async throws -> UUID {
        try await Task.sleep(for: .milliseconds(500))
        return UUID()
    }

    func pollInsight(jobID: UUID) async throws -> InsightPollStatus {
        // Longer delay in UI testing so XCUITest can observe the loading state
        let delay: Duration = ProcessInfo.processInfo.arguments.contains("UITesting")
            ? .seconds(3)
            : .milliseconds(300)
        try await Task.sleep(for: delay)
        return .complete(
            "Great effort today! Consistent volume like this builds a strong foundation — keep showing up and the PRs will follow."
        )
    }
}
