import Foundation
import PRLiftsCore
import SwiftData

public extension User {
    static func stub(
        id: UUID = UUID(),
        email: String? = "stub@example.com",
        displayName: String? = "Stub User",
        unitPreference: WeightUnit = .lbs,
        measurementUnit: MeasurementUnit = .cm,
        gender: Gender = .na,
        goal: UserGoal? = nil,
        betaTier: BetaTier = .none
    ) -> User {
        User(
            id: id,
            email: email,
            displayName: displayName,
            unitPreference: unitPreference,
            measurementUnit: measurementUnit,
            gender: gender,
            goal: goal,
            betaTier: betaTier
        )
    }
}

public extension Exercise {
    static func stub(
        id: UUID = UUID(),
        name: String = "Bench Press",
        category: ExerciseCategory = .strength,
        muscleGroup: MuscleGroup = .midChest,
        secondaryMuscleGroups: [MuscleGroup] = [.shoulders, .triceps],
        equipment: ExerciseEquipment = .barbell,
        isCustom: Bool = false
    ) -> Exercise {
        Exercise(
            id: id,
            name: name,
            category: category,
            muscleGroup: muscleGroup,
            secondaryMuscleGroups: secondaryMuscleGroups,
            equipment: equipment,
            isCustom: isCustom
        )
    }
}

public extension Workout {
    static func stub(
        id: UUID = UUID(),
        name: String? = "Morning Session",
        status: WorkoutStatus = .inProgress,
        type: WorkoutType = .adHoc,
        format: WorkoutFormat = .weightlifting,
        location: WorkoutLocation? = .gym
    ) -> Workout {
        Workout(
            id: id,
            name: name,
            status: status,
            type: type,
            format: format,
            location: location
        )
    }
}

public extension WorkoutExercise {
    static func stub(
        id: UUID = UUID(),
        orderIndex: Int = 0,
        restSeconds: Int? = 90
    ) -> WorkoutExercise {
        WorkoutExercise(
            id: id,
            orderIndex: orderIndex,
            restSeconds: restSeconds
        )
    }
}

public extension WorkoutSet {
    static func stub(
        id: UUID = UUID(),
        setNumber: Int = 1,
        setType: SetType = .normal,
        weight: Double? = 100.0,
        weightUnit: WeightUnit? = .lbs,
        reps: Int? = 10,
        isCompleted: Bool = true
    ) -> WorkoutSet {
        WorkoutSet(
            id: id,
            setNumber: setNumber,
            setType: setType,
            weight: weight,
            weightUnit: weightUnit,
            reps: reps,
            isCompleted: isCompleted
        )
    }
}

public extension PersonalRecord {
    static func stub(
        id: UUID = UUID(),
        weightModifier: WeightModifier = .none,
        recordType: RecordType = .heaviestWeight,
        value: Double = 225.0,
        valueUnit: ValueUnit? = .lbs,
        recordedAt: Date = Date(),
        previousValue: Double? = 205.0,
        workoutSetID: UUID = UUID()
    ) -> PersonalRecord {
        PersonalRecord(
            id: id,
            weightModifier: weightModifier,
            recordType: recordType,
            value: value,
            valueUnit: valueUnit,
            recordedAt: recordedAt,
            previousValue: previousValue,
            workoutSetID: workoutSetID
        )
    }
}

public extension Job {
    static func stub(
        id: UUID = UUID(),
        jobType: JobType = .insight,
        status: JobStatus = .pending,
        expiresAt: Date = Date().addingTimeInterval(300)
    ) -> Job {
        Job(
            id: id,
            jobType: jobType,
            status: status,
            expiresAt: expiresAt
        )
    }
}

public extension SyncEventLog {
    static func stub(
        id: UUID = UUID(),
        eventType: SyncEventType = .writeAttempt,
        entityType: SyncEntityType = .workout,
        entityID: UUID = UUID(),
        detail: String? = nil,
        occurredAt: Date = Date()
    ) -> SyncEventLog {
        SyncEventLog(
            id: id,
            eventType: eventType,
            entityType: entityType,
            entityID: entityID,
            detail: detail,
            occurredAt: occurredAt
        )
    }
}

public extension SupportReport {
    static func stub(
        id: UUID = UUID(),
        deviceModel: String = "iPhone SE (3rd generation)",
        iosVersion: String = "18.0",
        appVersion: String = "1.0.0",
        reportDescription: String = "App crashed on workout screen",
        syncLogUploaded: Bool = false
    ) -> SupportReport {
        SupportReport(
            id: id,
            deviceModel: deviceModel,
            iosVersion: iosVersion,
            appVersion: appVersion,
            reportDescription: reportDescription,
            syncLogUploaded: syncLogUploaded
        )
    }
}

public enum TestContainerFactory {
    public static func make() throws -> ModelContainer {
        let schema = Schema(PRLiftsSchema.models)
        let config = ModelConfiguration(schema: schema, isStoredInMemoryOnly: true)
        return try ModelContainer(for: schema, configurations: config)
    }
}
