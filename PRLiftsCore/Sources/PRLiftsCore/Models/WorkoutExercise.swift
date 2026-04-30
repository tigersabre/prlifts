import Foundation
import SwiftData

@Model
public final class WorkoutExercise {
    public var id: UUID
    public var orderIndex: Int
    public var notes: String?
    public var restSeconds: Int?
    public var createdAt: Date
    public var updatedAt: Date

    public var workout: Workout?
    public var exercise: Exercise?

    @Relationship(deleteRule: .cascade, inverse: \WorkoutSet.workoutExercise)
    public var sets: [WorkoutSet]

    public init(
        id: UUID = UUID(),
        orderIndex: Int,
        notes: String? = nil,
        restSeconds: Int? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.orderIndex = orderIndex
        self.notes = notes
        self.restSeconds = restSeconds
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.sets = []
    }
}
