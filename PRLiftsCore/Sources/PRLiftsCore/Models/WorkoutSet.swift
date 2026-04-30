import Foundation
import SwiftData

@Model
public final class WorkoutSet {
    public var id: UUID
    public var setNumber: Int
    public var setType: SetType
    public var weight: Double?
    public var weightUnit: WeightUnit?
    public var weightModifier: WeightModifier
    public var modifierValue: Double?
    public var modifierUnit: WeightUnit?
    public var reps: Int?
    public var durationSeconds: Int?
    public var distanceMeters: Double?
    public var calories: Int?
    public var rpe: Int?
    public var isCompleted: Bool
    public var notes: String?
    public var serverReceivedAt: Date
    public var createdAt: Date
    public var updatedAt: Date

    public var workoutExercise: WorkoutExercise?

    public init(
        id: UUID = UUID(),
        setNumber: Int,
        setType: SetType = .normal,
        weight: Double? = nil,
        weightUnit: WeightUnit? = nil,
        weightModifier: WeightModifier = .none,
        modifierValue: Double? = nil,
        modifierUnit: WeightUnit? = nil,
        reps: Int? = nil,
        durationSeconds: Int? = nil,
        distanceMeters: Double? = nil,
        calories: Int? = nil,
        rpe: Int? = nil,
        isCompleted: Bool = false,
        notes: String? = nil,
        serverReceivedAt: Date = Date(),
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.setNumber = setNumber
        self.setType = setType
        self.weight = weight
        self.weightUnit = weightUnit
        self.weightModifier = weightModifier
        self.modifierValue = modifierValue
        self.modifierUnit = modifierUnit
        self.reps = reps
        self.durationSeconds = durationSeconds
        self.distanceMeters = distanceMeters
        self.calories = calories
        self.rpe = rpe
        self.isCompleted = isCompleted
        self.notes = notes
        self.serverReceivedAt = serverReceivedAt
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}
