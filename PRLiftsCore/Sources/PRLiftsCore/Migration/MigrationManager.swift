import Foundation

public enum MigrationManager {
    public static let currentVersion = 1

    nonisolated(unsafe) static var userDefaults: UserDefaults = .standard

    private static var inProgressKey: String {
        "swiftdata_migration_in_progress_v\(currentVersion)"
    }

    public static var migrationFailed: Bool {
        userDefaults.bool(forKey: inProgressKey)
    }

    public static func beginMigration() {
        userDefaults.set(true, forKey: inProgressKey)
    }

    public static func completeMigration() {
        userDefaults.removeObject(forKey: inProgressKey)
    }

    public static func resetMigrationFlag() {
        userDefaults.removeObject(forKey: inProgressKey)
    }
}
