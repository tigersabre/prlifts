import Foundation

struct HomeStats: Equatable {
    let weeklyCount: Int
    let bestWeek: Int
    let totalWorkouts: Int
    let totalPrs: Int

    static let zero = HomeStats(weeklyCount: 0, bestWeek: 0, totalWorkouts: 0, totalPrs: 0)
}

protocol StatsServiceProtocol: Sendable {
    func fetchStats() async throws -> HomeStats
}

final class StubStatsService: StatsServiceProtocol {
    nonisolated init() {}

    func fetchStats() async throws -> HomeStats {
        let delay: Duration = ProcessInfo.processInfo.arguments.contains("UITesting")
            ? .seconds(3)
            : .milliseconds(300)
        try await Task.sleep(for: delay)
        return HomeStats(weeklyCount: 3, bestWeek: 5, totalWorkouts: 42, totalPrs: 7)
    }
}
