import Foundation
import PRLiftsCore

struct ExerciseSearchResult: Identifiable, Sendable {
    let id: UUID
    let name: String
    let category: ExerciseCategory
    let muscleGroup: MuscleGroup
    let equipment: ExerciseEquipment
}

protocol ExerciseServiceProtocol: Sendable {
    func search(query: String) async throws -> [ExerciseSearchResult]
}

final class StubExerciseService: ExerciseServiceProtocol {
    nonisolated init() {}

    func search(query: String) async throws -> [ExerciseSearchResult] {
        try await Task.sleep(for: .milliseconds(300))
        let q = query.lowercased()
        return _catalog.filter { $0.name.lowercased().contains(q) }
    }

    private let _catalog: [ExerciseSearchResult] = [
        ExerciseSearchResult(id: UUID(), name: "Bench Press", category: .strength, muscleGroup: .midChest, equipment: .barbell),
        ExerciseSearchResult(id: UUID(), name: "Squat", category: .strength, muscleGroup: .quads, equipment: .barbell),
        ExerciseSearchResult(id: UUID(), name: "Deadlift", category: .strength, muscleGroup: .lowerBack, equipment: .barbell),
        ExerciseSearchResult(id: UUID(), name: "Pull-Up", category: .strength, muscleGroup: .upperBack, equipment: .bodyweight),
        ExerciseSearchResult(id: UUID(), name: "Overhead Press", category: .strength, muscleGroup: .shoulders, equipment: .barbell),
        ExerciseSearchResult(id: UUID(), name: "Barbell Row", category: .strength, muscleGroup: .upperBack, equipment: .barbell),
        ExerciseSearchResult(id: UUID(), name: "Dumbbell Curl", category: .strength, muscleGroup: .biceps, equipment: .dumbbell),
        ExerciseSearchResult(id: UUID(), name: "Tricep Pushdown", category: .strength, muscleGroup: .triceps, equipment: .cable),
    ]
}
