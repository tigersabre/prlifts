import Foundation
import PRLiftsCore

@MainActor
@Observable
final class WorkoutInsightViewModel {

    // MARK: Phase

    enum Phase {
        case idle
        case requesting
        case polling
        case complete(String)
        case timeout
        case rateLimited
        case offline
    }

    private(set) var phase: Phase = .idle

    private let insightService: any InsightServiceProtocol
    private let networkMonitor: any NetworkPathMonitorProtocol
    private let pollInterval: Duration
    private var activeTask: Task<Void, Never>?

    // MARK: Init

    nonisolated init(
        insightService: any InsightServiceProtocol = StubInsightService(),
        networkMonitor: any NetworkPathMonitorProtocol = LiveNetworkPathMonitor(),
        pollInterval: Duration = .seconds(3)
    ) {
        self.insightService = insightService
        self.networkMonitor = networkMonitor
        self.pollInterval = pollInterval
    }

    // MARK: Trigger

    func trigger(
        workoutID: UUID,
        cachedInsight: String?,
        saveInsight: @escaping (String) -> Void
    ) {
        guard case .idle = phase else { return }

        if let cached = cachedInsight {
            phase = .complete(cached)
            return
        }

        phase = .requesting
        startRequest(workoutID: workoutID, saveInsight: saveInsight)
    }

    func retry(workoutID: UUID, saveInsight: @escaping (String) -> Void) {
        activeTask?.cancel()
        phase = .requesting
        startRequest(workoutID: workoutID, saveInsight: saveInsight)
    }

    // MARK: Private

    private func startRequest(workoutID: UUID, saveInsight: @escaping (String) -> Void) {
        activeTask = Task { [weak self] in
            await self?.performRequest(workoutID: workoutID, saveInsight: saveInsight)
        }
    }

    private func performRequest(workoutID: UUID, saveInsight: @escaping (String) -> Void) async {
        do {
            let jobID = try await insightService.requestInsight(workoutID: workoutID)
            phase = .polling
            await pollForResult(jobID: jobID, saveInsight: saveInsight)
        } catch InsightServiceError.rateLimited {
            phase = .rateLimited
        } catch InsightServiceError.networkError {
            phase = .offline
            waitForConnectivity(thenRetry: workoutID, saveInsight: saveInsight)
        } catch {
            phase = .timeout
        }
    }

    private func pollForResult(jobID: UUID, saveInsight: @escaping (String) -> Void) async {
        // Poll every pollInterval, up to 10 times (default 30s total)
        for _ in 0..<10 {
            do {
                try await Task.sleep(for: pollInterval)
            } catch {
                return // Task cancelled
            }
            guard !Task.isCancelled else { return }
            do {
                let status = try await insightService.pollInsight(jobID: jobID)
                switch status {
                case .complete(let text):
                    saveInsight(text)
                    phase = .complete(text)
                    return
                case .failed, .expired:
                    phase = .timeout
                    return
                case .pending, .processing:
                    continue
                }
            } catch {
                phase = .timeout
                return
            }
        }
        phase = .timeout
    }

    private func waitForConnectivity(thenRetry workoutID: UUID, saveInsight: @escaping (String) -> Void) {
        networkMonitor.setHandler { [weak self] status in
            guard status == .satisfied else { return }
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.networkMonitor.cancel()
                self.phase = .requesting
                await self.performRequest(workoutID: workoutID, saveInsight: saveInsight)
            }
        }
        networkMonitor.start(queue: .global())
    }
}

// MARK: Equatable

extension WorkoutInsightViewModel.Phase: Equatable {
    static func == (lhs: Self, rhs: Self) -> Bool {
        switch (lhs, rhs) {
        case (.idle, .idle), (.requesting, .requesting), (.polling, .polling),
             (.timeout, .timeout), (.rateLimited, .rateLimited), (.offline, .offline):
            return true
        case let (.complete(l), .complete(r)):
            return l == r
        default:
            return false
        }
    }
}
