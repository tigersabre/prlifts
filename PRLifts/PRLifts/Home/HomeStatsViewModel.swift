import Foundation
import SwiftData
import PRLiftsCore

@MainActor
@Observable
final class HomeStatsViewModel {

    enum Phase: Equatable {
        case loading
        case loaded(HomeStats)
    }

    private(set) var phase: Phase = .loading

    var isLoading: Bool {
        if case .loading = phase { return true }
        return false
    }

    var consistencyLine: String {
        switch phase {
        case .loading:
            return "— of — workouts this week."
        case .loaded(let stats):
            return "\(stats.weeklyCount) of \(stats.bestWeek) workouts this week."
        }
    }

    var filledSegments: Int {
        switch phase {
        case .loading: return 0
        case .loaded(let stats): return min(stats.weeklyCount, 7)
        }
    }

    private let statsService: any StatsServiceProtocol

    nonisolated init(statsService: any StatsServiceProtocol = StubStatsService()) {
        self.statsService = statsService
    }

    // Call from .task or .onAppear. Reads SwiftData cache synchronously then
    // refreshes from network in the background. Offline: cached values persist.
    func load(modelContext: ModelContext) {
        if let cached = loadFromCache(modelContext: modelContext) {
            phase = .loaded(cached)
        }

        Task { [weak self] in
            await self?.fetchAndCache(modelContext: modelContext)
        }
    }

    // MARK: Private

    private func loadFromCache(modelContext: ModelContext) -> HomeStats? {
        guard let row = try? modelContext.fetch(FetchDescriptor<UserStatsCache>()).first else {
            return nil
        }
        return HomeStats(
            weeklyCount: row.weeklyCount,
            bestWeek: row.bestWeek,
            totalWorkouts: row.totalWorkouts,
            totalPrs: row.totalPrs
        )
    }

    private func fetchAndCache(modelContext: ModelContext) async {
        do {
            let fresh = try await statsService.fetchStats()
            phase = .loaded(fresh)
            persistToCache(fresh, modelContext: modelContext)
        } catch {
            // Network failure: if cached values are already shown, keep them.
            // If still loading (no cache, first launch offline), show zeros.
            if case .loading = phase {
                phase = .loaded(.zero)
            }
        }
    }

    private func persistToCache(_ stats: HomeStats, modelContext: ModelContext) {
        let rows = (try? modelContext.fetch(FetchDescriptor<UserStatsCache>())) ?? []
        if let existing = rows.first {
            existing.weeklyCount = stats.weeklyCount
            existing.bestWeek = stats.bestWeek
            existing.totalWorkouts = stats.totalWorkouts
            existing.totalPrs = stats.totalPrs
            existing.cachedAt = Date()
        } else {
            modelContext.insert(UserStatsCache(
                weeklyCount: stats.weeklyCount,
                bestWeek: stats.bestWeek,
                totalWorkouts: stats.totalWorkouts,
                totalPrs: stats.totalPrs
            ))
        }
        try? modelContext.save()
    }
}
