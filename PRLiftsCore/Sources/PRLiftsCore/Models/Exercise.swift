import Foundation
import SwiftData

@Model
public final class Exercise {
    public var id: UUID
    public var name: String
    public var category: ExerciseCategory
    public var muscleGroup: MuscleGroup
    public var secondaryMuscleGroups: [MuscleGroup]
    public var equipment: ExerciseEquipment
    public var instructions: String?
    public var demoURL: String?
    public var isCustom: Bool
    public var createdBy: UUID?
    public var createdAt: Date
    public var updatedAt: Date

    @Relationship(deleteRule: .nullify, inverse: \WorkoutExercise.exercise)
    public var workoutExercises: [WorkoutExercise]

    @Relationship(deleteRule: .nullify, inverse: \PersonalRecord.exercise)
    public var personalRecords: [PersonalRecord]

    public init(
        id: UUID = UUID(),
        name: String,
        category: ExerciseCategory,
        muscleGroup: MuscleGroup,
        secondaryMuscleGroups: [MuscleGroup] = [],
        equipment: ExerciseEquipment,
        instructions: String? = nil,
        demoURL: String? = nil,
        isCustom: Bool = false,
        createdBy: UUID? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.category = category
        self.muscleGroup = muscleGroup
        self.secondaryMuscleGroups = secondaryMuscleGroups
        self.equipment = equipment
        self.instructions = instructions
        self.demoURL = demoURL
        self.isCustom = isCustom
        self.createdBy = createdBy
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.workoutExercises = []
        self.personalRecords = []
    }
}
