import Foundation
import SwiftData

public enum PRLiftsSchema {
    public static var models: [any PersistentModel.Type] {
        [
            User.self,
            Exercise.self,
            Workout.self,
            WorkoutExercise.self,
            WorkoutSet.self,
            PersonalRecord.self,
            Job.self,
            SyncEventLog.self
        ]
    }

    public static func makeContainer(inMemory: Bool = false) throws -> ModelContainer {
        MigrationManager.beginMigration()
        let schema = Schema(models)
        let config = ModelConfiguration(schema: schema, isStoredInMemoryOnly: inMemory)
        let container = try ModelContainer(for: schema, configurations: config)
        MigrationManager.completeMigration()
        return container
    }
}
