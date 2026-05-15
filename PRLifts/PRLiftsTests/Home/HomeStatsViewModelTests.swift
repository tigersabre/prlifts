import XCTest
import SwiftData
import PRLiftsCore
@testable import PRLifts

// MARK: - Fakes

private final class ImmediateStatsService: StatsServiceProtocol, @unchecked Sendable {
    let stats: HomeStats
    init(stats: HomeStats) { self.stats = stats }
    func fetchStats() async throws -> HomeStats { stats }
}

private final class FailingStatsService: StatsServiceProtocol, @unchecked Sendable {
    struct FakeNetworkError: Error {}
    func fetchStats() async throws -> HomeStats { throw FakeNetworkError() }
}

private final class SlowStatsService: StatsServiceProtocol, @unchecked Sendable {
    func fetchStats() async throws -> HomeStats {
        try await Task.sleep(for: .seconds(10))
        return .zero
    }
}

// MARK: - Tests

@MainActor
final class HomeStatsViewModelTests: XCTestCase {
    private var container: ModelContainer!

    override func setUp() async throws {
        container = try PRLiftsSchema.makeContainer(inMemory: true)
    }

    private var ctx: ModelContext { container.mainContext }

    // MARK: Initial state

    func test_phaseIsLoadingInitially() async throws {
        let sut = HomeStatsViewModel(statsService: SlowStatsService())
        XCTAssertEqual(sut.phase, .loading)
        try await Task.sleep(for: .milliseconds(50))
    }

    func test_isLoadingTrueInitially() async throws {
        let sut = HomeStatsViewModel(statsService: SlowStatsService())
        XCTAssertTrue(sut.isLoading)
        try await Task.sleep(for: .milliseconds(50))
    }

    // MARK: Cache loading

    func test_load_withCache_immediatelyShowsCachedStats() async throws {
        ctx.insert(UserStatsCache(weeklyCount: 3, bestWeek: 5, totalWorkouts: 42, totalPrs: 7))
        try ctx.save()

        let sut = HomeStatsViewModel(statsService: SlowStatsService())
        sut.load(modelContext: ctx)

        XCTAssertEqual(sut.phase, .loaded(HomeStats(weeklyCount: 3, bestWeek: 5, totalWorkouts: 42, totalPrs: 7)))
        try await Task.sleep(for: .milliseconds(50))
    }

    func test_load_withNoCache_startsLoading() async throws {
        let sut = HomeStatsViewModel(statsService: SlowStatsService())
        sut.load(modelContext: ctx)
        XCTAssertEqual(sut.phase, .loading)
        try await Task.sleep(for: .milliseconds(50))
    }

    // MARK: Successful fetch

    func test_load_activeUser_showsCorrectStats() async throws {
        let expected = HomeStats(weeklyCount: 3, bestWeek: 5, totalWorkouts: 42, totalPrs: 7)
        let sut = HomeStatsViewModel(statsService: ImmediateStatsService(stats: expected))
        sut.load(modelContext: ctx)
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(sut.phase, .loaded(expected))
    }

    func test_load_newUser_showsZeroState() async throws {
        let sut = HomeStatsViewModel(statsService: ImmediateStatsService(stats: .zero))
        sut.load(modelContext: ctx)
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(sut.phase, .loaded(.zero))
    }

    func test_load_success_persistsToCache() async throws {
        let expected = HomeStats(weeklyCount: 2, bestWeek: 4, totalWorkouts: 10, totalPrs: 1)
        let sut = HomeStatsViewModel(statsService: ImmediateStatsService(stats: expected))
        sut.load(modelContext: ctx)
        try await Task.sleep(for: .milliseconds(100))

        let rows = try ctx.fetch(FetchDescriptor<UserStatsCache>())
        XCTAssertEqual(rows.count, 1)
        XCTAssertEqual(rows[0].weeklyCount, 2)
        XCTAssertEqual(rows[0].bestWeek, 4)
    }

    func test_load_successTwice_updatesExistingCache() async throws {
        let sut = HomeStatsViewModel(statsService: ImmediateStatsService(stats: .zero))
        sut.load(modelContext: ctx)
        try await Task.sleep(for: .milliseconds(100))
        sut.load(modelContext: ctx)
        try await Task.sleep(for: .milliseconds(100))

        let rows = try ctx.fetch(FetchDescriptor<UserStatsCache>())
        XCTAssertEqual(rows.count, 1)
    }

    // MARK: Offline / error handling

    func test_load_offline_withCache_showsCachedValues() async throws {
        ctx.insert(UserStatsCache(weeklyCount: 2, bestWeek: 4, totalWorkouts: 20, totalPrs: 3))
        try ctx.save()

        let sut = HomeStatsViewModel(statsService: FailingStatsService())
        sut.load(modelContext: ctx)
        XCTAssertEqual(sut.phase, .loaded(HomeStats(weeklyCount: 2, bestWeek: 4, totalWorkouts: 20, totalPrs: 3)))
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(sut.phase, .loaded(HomeStats(weeklyCount: 2, bestWeek: 4, totalWorkouts: 20, totalPrs: 3)))
    }

    func test_load_offline_noCache_showsZeros() async throws {
        let sut = HomeStatsViewModel(statsService: FailingStatsService())
        sut.load(modelContext: ctx)
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(sut.phase, .loaded(.zero))
    }

    // MARK: Consistency line format

    func test_consistencyLine_whileLoading_showsPlaceholder() async throws {
        let sut = HomeStatsViewModel(statsService: SlowStatsService())
        XCTAssertEqual(sut.consistencyLine, "— of — workouts this week.")
        try await Task.sleep(for: .milliseconds(50))
    }

    func test_consistencyLine_activeUser_showsCorrectFormat() async throws {
        let sut = HomeStatsViewModel(statsService: ImmediateStatsService(
            stats: HomeStats(weeklyCount: 3, bestWeek: 5, totalWorkouts: 42, totalPrs: 7)
        ))
        sut.load(modelContext: ctx)
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(sut.consistencyLine, "3 of 5 workouts this week.")
    }

    func test_consistencyLine_newUser_showsZeroFormat() async throws {
        let sut = HomeStatsViewModel(statsService: ImmediateStatsService(stats: .zero))
        sut.load(modelContext: ctx)
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(sut.consistencyLine, "0 of 0 workouts this week.")
    }

    // MARK: filledSegments

    func test_filledSegments_whileLoading_isZero() async throws {
        let sut = HomeStatsViewModel(statsService: SlowStatsService())
        XCTAssertEqual(sut.filledSegments, 0)
        try await Task.sleep(for: .milliseconds(50))
    }

    func test_filledSegments_capsAtSeven() async throws {
        let sut = HomeStatsViewModel(statsService: ImmediateStatsService(
            stats: HomeStats(weeklyCount: 10, bestWeek: 10, totalWorkouts: 50, totalPrs: 5)
        ))
        sut.load(modelContext: ctx)
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(sut.filledSegments, 7)
    }
}
