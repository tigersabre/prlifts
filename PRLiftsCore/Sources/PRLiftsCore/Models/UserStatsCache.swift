import Foundation
import SwiftData

// Client-only cache for GET /v1/stats response. Not a backend table mapping —
// not included in SchemaMapping. One row per installation; upserted on each
// successful fetch.
@Model
public final class UserStatsCache {
    public var weeklyCount: Int
    public var bestWeek: Int
    public var totalWorkouts: Int
    public var totalPrs: Int
    public var cachedAt: Date

    public init(
        weeklyCount: Int = 0,
        bestWeek: Int = 0,
        totalWorkouts: Int = 0,
        totalPrs: Int = 0,
        cachedAt: Date = Date()
    ) {
        self.weeklyCount = weeklyCount
        self.bestWeek = bestWeek
        self.totalWorkouts = totalWorkouts
        self.totalPrs = totalPrs
        self.cachedAt = cachedAt
    }
}
