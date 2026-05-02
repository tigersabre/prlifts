import Foundation
import SwiftData

@Model
public final class Workout {
    public var id: UUID
    public var name: String?
    public var notes: String?
    public var status: WorkoutStatus
    public var type: WorkoutType
    public var format: WorkoutFormat
    // V2: will reference WorkoutPlan when the plan model is introduced.
    public var planID: UUID?
    public var startedAt: Date
    public var completedAt: Date?
    public var durationSeconds: Int?
    public var location: WorkoutLocation?
    public var rating: Int?
    public var serverReceivedAt: Date
    public var createdAt: Date
    public var updatedAt: Date

    public var user: User?

    @Relationship(deleteRule: .cascade, inverse: \WorkoutExercise.workout)
    public var exercises: [WorkoutExercise]

    public init(
        id: UUID = UUID(),
        name: String? = nil,
        notes: String? = nil,
        status: WorkoutStatus = .inProgress,
        type: WorkoutType,
        format: WorkoutFormat,
        planID: UUID? = nil,
        startedAt: Date = Date(),
        completedAt: Date? = nil,
        durationSeconds: Int? = nil,
        location: WorkoutLocation? = nil,
        rating: Int? = nil,
        serverReceivedAt: Date = Date(),
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.notes = notes
        self.status = status
        self.type = type
        self.format = format
        self.planID = planID
        self.startedAt = startedAt
        self.completedAt = completedAt
        self.durationSeconds = durationSeconds
        self.location = location
        self.rating = rating
        self.serverReceivedAt = serverReceivedAt
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.exercises = []
    }
}
