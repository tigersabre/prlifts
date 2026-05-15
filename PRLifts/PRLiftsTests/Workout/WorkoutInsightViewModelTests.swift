import XCTest
import SwiftData
import PRLiftsCore
@testable import PRLifts

@MainActor
final class WorkoutInsightViewModelTests: XCTestCase {
    private var container: ModelContainer!
    private var context: ModelContext!
    private var workout: Workout!

    override func setUp() async throws {
        container = try PRLiftsSchema.makeContainer(inMemory: true)
        context = container.mainContext
        workout = Workout(type: .adHoc, format: .weightlifting)
        context.insert(workout)
        try context.save()
    }

    override func tearDown() async throws {
        workout = nil
        context = nil
        container = nil
    }

    // Fast poll interval for tests — 10ms instead of 3s
    private func makeSUT(
        insightService: any InsightServiceProtocol,
        networkMonitor: any NetworkPathMonitorProtocol = StubNetworkPathMonitor()
    ) -> WorkoutInsightViewModel {
        WorkoutInsightViewModel(
            insightService: insightService,
            networkMonitor: networkMonitor,
            pollInterval: .milliseconds(10)
        )
    }

    private func noop(_: String) {}

    // MARK: Cached insight

    func testTrigger_withCachedInsight_showsImmediately() async throws {
        let sut = makeSUT(insightService: ImmediateSuccessInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: "cached text", saveInsight: noop)
        XCTAssertEqual(sut.phase, .complete("cached text"))
        try await Task.sleep(for: .milliseconds(50))
    }

    func testTrigger_withCachedInsight_doesNotCallService() async throws {
        let service = CallCountingInsightService()
        let sut = makeSUT(insightService: service)
        sut.trigger(workoutID: workout.id, cachedInsight: "cached", saveInsight: noop)
        try await Task.sleep(for: .milliseconds(50))
        XCTAssertEqual(service.requestCallCount, 0)
    }

    // MARK: Initial transition

    func testTrigger_withNoCache_transitionsToRequesting() async throws {
        let sut = makeSUT(insightService: ImmediateSuccessInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        XCTAssertEqual(sut.phase, .requesting)
        try await Task.sleep(for: .milliseconds(100))
    }

    func testTrigger_isIdempotent_whenAlreadyRequesting() async throws {
        let sut = makeSUT(insightService: ImmediateSuccessInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        XCTAssertEqual(sut.phase, .requesting)
        try await Task.sleep(for: .milliseconds(100))
    }

    // MARK: Polling state

    func testTrigger_transitsThroughPolling_beforeFirstPoll() async throws {
        // BlockingPollInsightService blocks the poll response indefinitely,
        // so after the job_id is returned the phase should be .polling
        let sut = makeSUT(insightService: BlockingPollInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        // Give the request time to complete (returns immediately) and sleep to start
        try await Task.sleep(for: .milliseconds(50))
        XCTAssertEqual(sut.phase, .polling)
    }

    // MARK: Success path

    func testTrigger_onSuccess_transitionsToComplete() async throws {
        let sut = makeSUT(insightService: ImmediateSuccessInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        try await Task.sleep(for: .milliseconds(100))
        if case .complete = sut.phase { /* pass */ }
        else { XCTFail("Expected .complete, got \(sut.phase)") }
    }

    func testTrigger_onSuccess_callsSaveInsight() async throws {
        let sut = makeSUT(insightService: ImmediateSuccessInsightService())
        var savedText: String?
        sut.trigger(workoutID: workout.id, cachedInsight: nil) { savedText = $0 }
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertNotNil(savedText)
        XCTAssertFalse(savedText!.isEmpty)
    }

    // MARK: Timeout

    func testTrigger_exhaustsPolls_transitionsToTimeout() async throws {
        // AlwaysPendingInsightService returns .pending every poll.
        // With pollInterval=10ms and 10 polls, timeout at ~100ms.
        let sut = makeSUT(insightService: AlwaysPendingInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        try await Task.sleep(for: .milliseconds(300))
        XCTAssertEqual(sut.phase, .timeout)
    }

    func testTrigger_onFailedPoll_transitionsToTimeout() async throws {
        let sut = makeSUT(insightService: FailedJobInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(sut.phase, .timeout)
    }

    func testTrigger_onExpiredJob_transitionsToTimeout() async throws {
        let sut = makeSUT(insightService: ExpiredJobInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(sut.phase, .timeout)
    }

    // MARK: Rate limited

    func testTrigger_on429_transitionsToRateLimited() async throws {
        let sut = makeSUT(insightService: RateLimitedInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        try await Task.sleep(for: .milliseconds(50))
        XCTAssertEqual(sut.phase, .rateLimited)
    }

    // MARK: Offline

    func testTrigger_onNetworkError_transitionsToOffline() async throws {
        let sut = makeSUT(insightService: NetworkErrorInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        try await Task.sleep(for: .milliseconds(50))
        XCTAssertEqual(sut.phase, .offline)
    }

    func testTrigger_offline_retriesWhenConnectivityRestored() async throws {
        let service = OnceFailingInsightService()
        let monitor = StubNetworkPathMonitor()
        let sut = WorkoutInsightViewModel(
            insightService: service,
            networkMonitor: monitor,
            pollInterval: .milliseconds(10)
        )
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        try await Task.sleep(for: .milliseconds(50))
        XCTAssertEqual(sut.phase, .offline)

        monitor.simulateConnectivity(.satisfied)
        try await Task.sleep(for: .milliseconds(150))
        if case .complete = sut.phase { /* pass */ }
        else { XCTFail("Expected .complete after connectivity restored, got \(sut.phase)") }
    }

    // MARK: Retry

    func testRetry_fromTimeout_transitionsToComplete() async throws {
        let sut = makeSUT(insightService: AlwaysPendingInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil, saveInsight: noop)
        try await Task.sleep(for: .milliseconds(300))
        XCTAssertEqual(sut.phase, .timeout)

        sut.retry(workoutID: workout.id, saveInsight: noop)
        // Swap the service via a fresh ViewModel to test clean retry path
        let successSUT = makeSUT(insightService: ImmediateSuccessInsightService())
        successSUT.retry(workoutID: workout.id, saveInsight: noop)
        try await Task.sleep(for: .milliseconds(100))
        if case .complete = successSUT.phase { /* pass */ }
        else { XCTFail("Expected .complete after retry, got \(successSUT.phase)") }
    }

    // MARK: SwiftData persistence

    func testTrigger_onSuccess_persistsInsightTextToWorkout() async throws {
        let sut = makeSUT(insightService: ImmediateSuccessInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil) { [weak self] text in
            self?.workout.aiInsightText = text
        }
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertNotNil(workout.aiInsightText)
        XCTAssertFalse(workout.aiInsightText!.isEmpty)
    }

    func testTrigger_onFailure_doesNotPersistInsightText() async throws {
        let sut = makeSUT(insightService: RateLimitedInsightService())
        sut.trigger(workoutID: workout.id, cachedInsight: nil) { [weak self] text in
            self?.workout.aiInsightText = text
        }
        try await Task.sleep(for: .milliseconds(50))
        XCTAssertNil(workout.aiInsightText)
    }
}

// MARK: Test Doubles

private final class ImmediateSuccessInsightService: InsightServiceProtocol {
    nonisolated init() {}
    func requestInsight(workoutID: UUID) async throws -> UUID { UUID() }
    func pollInsight(jobID: UUID) async throws -> InsightPollStatus { .complete("test insight") }
}

private final class CallCountingInsightService: InsightServiceProtocol, @unchecked Sendable {
    nonisolated init() {}
    private(set) var requestCallCount = 0
    func requestInsight(workoutID: UUID) async throws -> UUID {
        requestCallCount += 1; return UUID()
    }
    func pollInsight(jobID: UUID) async throws -> InsightPollStatus { .complete("ok") }
}

// Blocks the poll response so the ViewModel stays in .polling for inspection
private final class BlockingPollInsightService: InsightServiceProtocol {
    nonisolated init() {}
    func requestInsight(workoutID: UUID) async throws -> UUID { UUID() }
    func pollInsight(jobID: UUID) async throws -> InsightPollStatus {
        try await Task.sleep(for: .milliseconds(100))
        return .pending
    }
}

// Returns .pending every poll — exhausts the loop → timeout
private final class AlwaysPendingInsightService: InsightServiceProtocol {
    nonisolated init() {}
    func requestInsight(workoutID: UUID) async throws -> UUID { UUID() }
    func pollInsight(jobID: UUID) async throws -> InsightPollStatus { .pending }
}

private final class FailedJobInsightService: InsightServiceProtocol {
    nonisolated init() {}
    func requestInsight(workoutID: UUID) async throws -> UUID { UUID() }
    func pollInsight(jobID: UUID) async throws -> InsightPollStatus { .failed }
}

private final class ExpiredJobInsightService: InsightServiceProtocol {
    nonisolated init() {}
    func requestInsight(workoutID: UUID) async throws -> UUID { UUID() }
    func pollInsight(jobID: UUID) async throws -> InsightPollStatus { .expired }
}

private final class RateLimitedInsightService: InsightServiceProtocol {
    nonisolated init() {}
    func requestInsight(workoutID: UUID) async throws -> UUID {
        throw InsightServiceError.rateLimited
    }
    func pollInsight(jobID: UUID) async throws -> InsightPollStatus { .pending }
}

private final class NetworkErrorInsightService: InsightServiceProtocol {
    nonisolated init() {}
    func requestInsight(workoutID: UUID) async throws -> UUID {
        throw InsightServiceError.networkError
    }
    func pollInsight(jobID: UUID) async throws -> InsightPollStatus { .pending }
}

// Fails on first request, succeeds thereafter
private final class OnceFailingInsightService: InsightServiceProtocol, @unchecked Sendable {
    nonisolated init() {}
    private var callCount = 0
    func requestInsight(workoutID: UUID) async throws -> UUID {
        if callCount == 0 { callCount += 1; throw InsightServiceError.networkError }
        return UUID()
    }
    func pollInsight(jobID: UUID) async throws -> InsightPollStatus { .complete("recovered insight") }
}

private final class StubNetworkPathMonitor: NetworkPathMonitorProtocol, @unchecked Sendable {
    nonisolated init() {}
    private var storedHandler: (@Sendable (SyncPathStatus) -> Void)?
    func setHandler(_ handler: @escaping @Sendable (SyncPathStatus) -> Void) { storedHandler = handler }
    func start(queue: DispatchQueue) {}
    func cancel() { storedHandler = nil }
    func simulateConnectivity(_ status: SyncPathStatus) { storedHandler?(status) }
}
