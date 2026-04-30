import Foundation

public enum WeightUnit: String, Codable, CaseIterable, Hashable, Sendable {
    case kg
    case lbs
}

public enum MeasurementUnit: String, Codable, CaseIterable, Hashable, Sendable {
    case cm
    case inches
}

public enum Gender: String, Codable, CaseIterable, Hashable, Sendable {
    case male
    case female
    case na
}

public enum UserGoal: String, Codable, CaseIterable, Hashable, Sendable {
    case buildMuscle = "build_muscle"
    case loseFat = "lose_fat"
    case improveEndurance = "improve_endurance"
    case athleticPerformance = "athletic_performance"
    case generalFitness = "general_fitness"
}

public enum BetaTier: String, Codable, CaseIterable, Hashable, Sendable {
    case none
    case tester
    case fullAccess = "full_access"
}

public enum WorkoutStatus: String, Codable, CaseIterable, Hashable, Sendable {
    case inProgress = "in_progress"
    case paused
    case partialCompletion = "partial_completion"
    case completed
}

public enum WorkoutType: String, Codable, CaseIterable, Hashable, Sendable {
    case adHoc = "ad_hoc"
    case planned
}

public enum WorkoutFormat: String, Codable, CaseIterable, Hashable, Sendable {
    case weightlifting
    case cardio
    case mixed
    case other
}

public enum WorkoutLocation: String, Codable, CaseIterable, Hashable, Sendable {
    case gym
    case home
    case outdoor
    case other
}

public enum SetType: String, Codable, CaseIterable, Hashable, Sendable {
    case normal
    case warmup
    case dropset
    case failure
    case pr
}

public enum WeightModifier: String, Codable, CaseIterable, Hashable, Sendable {
    case none
    case assisted
    case weighted
}

public enum RecordType: String, Codable, CaseIterable, Hashable, Sendable {
    case heaviestWeight = "heaviest_weight"
    case mostReps = "most_reps"
    case longestDuration = "longest_duration"
    case longestDistance = "longest_distance"
    case bestRpe = "best_rpe"
}

public enum ValueUnit: String, Codable, CaseIterable, Hashable, Sendable {
    case kg
    case lbs
    case reps
    case seconds
    case meters
}

public enum ExerciseCategory: String, Codable, CaseIterable, Hashable, Sendable {
    case strength
    case cardio
    case flexibility
    case bodyweight
    case mobility
    case saq
    case rehab
}

public enum ExerciseEquipment: String, Codable, CaseIterable, Hashable, Sendable {
    case barbell
    case dumbbell
    case kettlebell
    case machine
    case cable
    case bodyweight
    case cardioMachine = "cardio_machine"
    case other
}

public enum MuscleGroup: String, Codable, CaseIterable, Hashable, Sendable {
    case upperChest = "upper_chest"
    case midChest = "mid_chest"
    case lowerChest = "lower_chest"
    case upperBack = "upper_back"
    case lowerBack = "lower_back"
    case shoulders
    case biceps
    case triceps
    case quads
    case hamstrings
    case calves
    case glutes
    case abs
    case obliques
    case fullBody = "full_body"
}

public enum JobStatus: String, Codable, CaseIterable, Hashable, Sendable {
    case pending
    case processing
    case complete
    case failed
    case expired
}

public enum JobType: String, Codable, CaseIterable, Hashable, Sendable {
    case insight
    case futureSelf = "future_self"
    case benchmarking
}

public enum SyncEventType: String, Codable, CaseIterable, Hashable, Sendable {
    case writeAttempt = "write_attempt"
    case syncAttempt = "sync_attempt"
    case syncSuccess = "sync_success"
    case syncFailure = "sync_failure"
    case conflictResolved = "conflict_resolved"
}

public enum SyncEntityType: String, Codable, CaseIterable, Hashable, Sendable {
    case workout
    case workoutExercise = "workout_exercise"
    case workoutSet = "workout_set"
    case personalRecord = "personal_record"
    case bodyMetrics = "body_metrics"
    case stepsEntry = "steps_entry"
}
