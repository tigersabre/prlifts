import Foundation

// MARK: - Schema Mapping Registry
//
// Declarative registry of PostgreSQL → SwiftData column mappings.
// Validated by backend/scripts/validate_schema_mapping.py as part of backend-ci.
//
// Rules:
//  - Every [iOS]-annotated column in docs/SCHEMA.md must have an entry here.
//  - [BE] columns must never appear here.
//  - swiftProperty must be the lowerCamelCase equivalent of the pg_column name.
//  - swiftType must be compatible with the PostgreSQL type.
//
// Do not edit without a corresponding SCHEMA.md update in the same PR.

public enum SchemaMapping {
    public struct Column: Sendable {
        public let table: String
        public let pgColumn: String
        public let pgType: String
        public let swiftModel: String
        public let swiftProperty: String
        public let swiftType: String
    }

    public static let columns: [Column] = [

        // MARK: - user

        Column(table: "user", pgColumn: "id",                   pgType: "UUID",         swiftModel: "User", swiftProperty: "id",                  swiftType: "UUID"),
        Column(table: "user", pgColumn: "email",                pgType: "TEXT",         swiftModel: "User", swiftProperty: "email",               swiftType: "String?"),
        Column(table: "user", pgColumn: "display_name",         pgType: "TEXT",         swiftModel: "User", swiftProperty: "displayName",         swiftType: "String?"),
        Column(table: "user", pgColumn: "avatar_url",           pgType: "TEXT",         swiftModel: "User", swiftProperty: "avatarURL",           swiftType: "String?"),
        Column(table: "user", pgColumn: "unit_preference",      pgType: "weight_unit",  swiftModel: "User", swiftProperty: "unitPreference",      swiftType: "WeightUnit"),
        Column(table: "user", pgColumn: "measurement_unit",     pgType: "measurement_unit", swiftModel: "User", swiftProperty: "measurementUnit", swiftType: "MeasurementUnit"),
        Column(table: "user", pgColumn: "date_of_birth",        pgType: "DATE",         swiftModel: "User", swiftProperty: "dateOfBirth",         swiftType: "Date?"),
        Column(table: "user", pgColumn: "gender",               pgType: "gender",       swiftModel: "User", swiftProperty: "gender",              swiftType: "Gender"),
        Column(table: "user", pgColumn: "goal",                 pgType: "user_goal",    swiftModel: "User", swiftProperty: "goal",                swiftType: "UserGoal?"),
        Column(table: "user", pgColumn: "phase_2_completed_at", pgType: "TIMESTAMPTZ",  swiftModel: "User", swiftProperty: "phase2CompletedAt",   swiftType: "Date?"),
        Column(table: "user", pgColumn: "beta_tier",            pgType: "beta_tier",    swiftModel: "User", swiftProperty: "betaTier",            swiftType: "BetaTier"),
        Column(table: "user", pgColumn: "created_at",           pgType: "TIMESTAMPTZ",  swiftModel: "User", swiftProperty: "createdAt",           swiftType: "Date"),
        Column(table: "user", pgColumn: "updated_at",           pgType: "TIMESTAMPTZ",  swiftModel: "User", swiftProperty: "updatedAt",           swiftType: "Date"),

        // MARK: - exercise

        Column(table: "exercise", pgColumn: "id",                       pgType: "UUID",             swiftModel: "Exercise", swiftProperty: "id",                     swiftType: "UUID"),
        Column(table: "exercise", pgColumn: "name",                     pgType: "TEXT",             swiftModel: "Exercise", swiftProperty: "name",                   swiftType: "String"),
        Column(table: "exercise", pgColumn: "category",                 pgType: "exercise_category", swiftModel: "Exercise", swiftProperty: "category",             swiftType: "ExerciseCategory"),
        Column(table: "exercise", pgColumn: "muscle_group",             pgType: "muscle_group",     swiftModel: "Exercise", swiftProperty: "muscleGroup",            swiftType: "MuscleGroup"),
        Column(table: "exercise", pgColumn: "secondary_muscle_groups",  pgType: "muscle_group[]",   swiftModel: "Exercise", swiftProperty: "secondaryMuscleGroups",  swiftType: "[MuscleGroup]"),
        Column(table: "exercise", pgColumn: "equipment",                pgType: "exercise_equipment", swiftModel: "Exercise", swiftProperty: "equipment",           swiftType: "ExerciseEquipment"),
        Column(table: "exercise", pgColumn: "instructions",             pgType: "TEXT",             swiftModel: "Exercise", swiftProperty: "instructions",           swiftType: "String?"),
        Column(table: "exercise", pgColumn: "demo_url",                 pgType: "TEXT",             swiftModel: "Exercise", swiftProperty: "demoURL",               swiftType: "String?"),
        Column(table: "exercise", pgColumn: "is_custom",                pgType: "BOOLEAN",          swiftModel: "Exercise", swiftProperty: "isCustom",              swiftType: "Bool"),
        Column(table: "exercise", pgColumn: "created_by",               pgType: "UUID",             swiftModel: "Exercise", swiftProperty: "createdBy",             swiftType: "UUID?"),
        Column(table: "exercise", pgColumn: "created_at",               pgType: "TIMESTAMPTZ",      swiftModel: "Exercise", swiftProperty: "createdAt",             swiftType: "Date"),
        Column(table: "exercise", pgColumn: "updated_at",               pgType: "TIMESTAMPTZ",      swiftModel: "Exercise", swiftProperty: "updatedAt",             swiftType: "Date"),

        // MARK: - workout
        // server_received_at is [BE] — omitted intentionally.

        Column(table: "workout", pgColumn: "id",               pgType: "UUID",            swiftModel: "Workout", swiftProperty: "id",              swiftType: "UUID"),
        Column(table: "workout", pgColumn: "user_id",          pgType: "UUID",            swiftModel: "Workout", swiftProperty: "user",            swiftType: "User?"),
        Column(table: "workout", pgColumn: "name",             pgType: "TEXT",            swiftModel: "Workout", swiftProperty: "name",            swiftType: "String?"),
        Column(table: "workout", pgColumn: "notes",            pgType: "TEXT",            swiftModel: "Workout", swiftProperty: "notes",           swiftType: "String?"),
        Column(table: "workout", pgColumn: "status",           pgType: "workout_status",  swiftModel: "Workout", swiftProperty: "status",          swiftType: "WorkoutStatus"),
        Column(table: "workout", pgColumn: "type",             pgType: "workout_type",    swiftModel: "Workout", swiftProperty: "type",            swiftType: "WorkoutType"),
        Column(table: "workout", pgColumn: "format",           pgType: "workout_format",  swiftModel: "Workout", swiftProperty: "format",          swiftType: "WorkoutFormat"),
        Column(table: "workout", pgColumn: "plan_id",          pgType: "UUID",            swiftModel: "Workout", swiftProperty: "planID",          swiftType: "UUID?"),
        Column(table: "workout", pgColumn: "started_at",       pgType: "TIMESTAMPTZ",     swiftModel: "Workout", swiftProperty: "startedAt",       swiftType: "Date"),
        Column(table: "workout", pgColumn: "completed_at",     pgType: "TIMESTAMPTZ",     swiftModel: "Workout", swiftProperty: "completedAt",     swiftType: "Date?"),
        Column(table: "workout", pgColumn: "duration_seconds", pgType: "INTEGER",         swiftModel: "Workout", swiftProperty: "durationSeconds", swiftType: "Int?"),
        Column(table: "workout", pgColumn: "location",         pgType: "workout_location", swiftModel: "Workout", swiftProperty: "location",       swiftType: "WorkoutLocation?"),
        Column(table: "workout", pgColumn: "rating",           pgType: "SMALLINT",        swiftModel: "Workout", swiftProperty: "rating",          swiftType: "Int?"),
        Column(table: "workout", pgColumn: "created_at",       pgType: "TIMESTAMPTZ",     swiftModel: "Workout", swiftProperty: "createdAt",       swiftType: "Date"),
        Column(table: "workout", pgColumn: "updated_at",       pgType: "TIMESTAMPTZ",     swiftModel: "Workout", swiftProperty: "updatedAt",       swiftType: "Date"),

        // MARK: - workout_exercise

        Column(table: "workout_exercise", pgColumn: "id",          pgType: "UUID",      swiftModel: "WorkoutExercise", swiftProperty: "id",          swiftType: "UUID"),
        Column(table: "workout_exercise", pgColumn: "workout_id",  pgType: "UUID",      swiftModel: "WorkoutExercise", swiftProperty: "workout",     swiftType: "Workout?"),
        Column(table: "workout_exercise", pgColumn: "exercise_id", pgType: "UUID",      swiftModel: "WorkoutExercise", swiftProperty: "exercise",    swiftType: "Exercise?"),
        Column(table: "workout_exercise", pgColumn: "order_index", pgType: "INTEGER",   swiftModel: "WorkoutExercise", swiftProperty: "orderIndex",  swiftType: "Int"),
        Column(table: "workout_exercise", pgColumn: "notes",       pgType: "TEXT",      swiftModel: "WorkoutExercise", swiftProperty: "notes",       swiftType: "String?"),
        Column(table: "workout_exercise", pgColumn: "rest_seconds", pgType: "INTEGER",  swiftModel: "WorkoutExercise", swiftProperty: "restSeconds", swiftType: "Int?"),
        Column(table: "workout_exercise", pgColumn: "created_at",  pgType: "TIMESTAMPTZ", swiftModel: "WorkoutExercise", swiftProperty: "createdAt", swiftType: "Date"),
        Column(table: "workout_exercise", pgColumn: "updated_at",  pgType: "TIMESTAMPTZ", swiftModel: "WorkoutExercise", swiftProperty: "updatedAt", swiftType: "Date"),

        // MARK: - workout_set
        // server_received_at is [BE] — omitted intentionally.

        Column(table: "workout_set", pgColumn: "id",                   pgType: "UUID",           swiftModel: "WorkoutSet", swiftProperty: "id",                  swiftType: "UUID"),
        Column(table: "workout_set", pgColumn: "workout_exercise_id",  pgType: "UUID",           swiftModel: "WorkoutSet", swiftProperty: "workoutExercise",     swiftType: "WorkoutExercise?"),
        Column(table: "workout_set", pgColumn: "set_number",           pgType: "INTEGER",        swiftModel: "WorkoutSet", swiftProperty: "setNumber",           swiftType: "Int"),
        Column(table: "workout_set", pgColumn: "set_type",             pgType: "set_type",       swiftModel: "WorkoutSet", swiftProperty: "setType",             swiftType: "SetType"),
        Column(table: "workout_set", pgColumn: "weight",               pgType: "NUMERIC",        swiftModel: "WorkoutSet", swiftProperty: "weight",              swiftType: "Double?"),
        Column(table: "workout_set", pgColumn: "weight_unit",          pgType: "weight_unit",    swiftModel: "WorkoutSet", swiftProperty: "weightUnit",          swiftType: "WeightUnit?"),
        Column(table: "workout_set", pgColumn: "weight_modifier",      pgType: "weight_modifier", swiftModel: "WorkoutSet", swiftProperty: "weightModifier",    swiftType: "WeightModifier"),
        Column(table: "workout_set", pgColumn: "modifier_value",       pgType: "NUMERIC",        swiftModel: "WorkoutSet", swiftProperty: "modifierValue",       swiftType: "Double?"),
        Column(table: "workout_set", pgColumn: "modifier_unit",        pgType: "weight_unit",    swiftModel: "WorkoutSet", swiftProperty: "modifierUnit",        swiftType: "WeightUnit?"),
        Column(table: "workout_set", pgColumn: "reps",                 pgType: "INTEGER",        swiftModel: "WorkoutSet", swiftProperty: "reps",                swiftType: "Int?"),
        Column(table: "workout_set", pgColumn: "duration_seconds",     pgType: "INTEGER",        swiftModel: "WorkoutSet", swiftProperty: "durationSeconds",     swiftType: "Int?"),
        Column(table: "workout_set", pgColumn: "distance_meters",      pgType: "NUMERIC",        swiftModel: "WorkoutSet", swiftProperty: "distanceMeters",      swiftType: "Double?"),
        Column(table: "workout_set", pgColumn: "calories",             pgType: "INTEGER",        swiftModel: "WorkoutSet", swiftProperty: "calories",            swiftType: "Int?"),
        Column(table: "workout_set", pgColumn: "rpe",                  pgType: "SMALLINT",       swiftModel: "WorkoutSet", swiftProperty: "rpe",                 swiftType: "Int?"),
        Column(table: "workout_set", pgColumn: "is_completed",         pgType: "BOOLEAN",        swiftModel: "WorkoutSet", swiftProperty: "isCompleted",         swiftType: "Bool"),
        Column(table: "workout_set", pgColumn: "notes",                pgType: "TEXT",           swiftModel: "WorkoutSet", swiftProperty: "notes",               swiftType: "String?"),
        Column(table: "workout_set", pgColumn: "created_at",           pgType: "TIMESTAMPTZ",    swiftModel: "WorkoutSet", swiftProperty: "createdAt",           swiftType: "Date"),
        Column(table: "workout_set", pgColumn: "updated_at",           pgType: "TIMESTAMPTZ",    swiftModel: "WorkoutSet", swiftProperty: "updatedAt",           swiftType: "Date"),

        // MARK: - personal_record

        Column(table: "personal_record", pgColumn: "id",                   pgType: "UUID",           swiftModel: "PersonalRecord", swiftProperty: "id",                  swiftType: "UUID"),
        Column(table: "personal_record", pgColumn: "user_id",              pgType: "UUID",           swiftModel: "PersonalRecord", swiftProperty: "user",                swiftType: "User?"),
        Column(table: "personal_record", pgColumn: "exercise_id",          pgType: "UUID",           swiftModel: "PersonalRecord", swiftProperty: "exercise",            swiftType: "Exercise?"),
        Column(table: "personal_record", pgColumn: "workout_set_id",       pgType: "UUID",           swiftModel: "PersonalRecord", swiftProperty: "workoutSetID",        swiftType: "UUID"),
        Column(table: "personal_record", pgColumn: "weight_modifier",      pgType: "weight_modifier", swiftModel: "PersonalRecord", swiftProperty: "weightModifier",    swiftType: "WeightModifier"),
        Column(table: "personal_record", pgColumn: "record_type",          pgType: "record_type",    swiftModel: "PersonalRecord", swiftProperty: "recordType",          swiftType: "RecordType"),
        Column(table: "personal_record", pgColumn: "value",                pgType: "NUMERIC",        swiftModel: "PersonalRecord", swiftProperty: "value",               swiftType: "Double"),
        Column(table: "personal_record", pgColumn: "value_unit",           pgType: "value_unit",     swiftModel: "PersonalRecord", swiftProperty: "valueUnit",           swiftType: "ValueUnit?"),
        Column(table: "personal_record", pgColumn: "recorded_at",          pgType: "TIMESTAMPTZ",    swiftModel: "PersonalRecord", swiftProperty: "recordedAt",          swiftType: "Date"),
        Column(table: "personal_record", pgColumn: "previous_value",       pgType: "NUMERIC",        swiftModel: "PersonalRecord", swiftProperty: "previousValue",       swiftType: "Double?"),
        Column(table: "personal_record", pgColumn: "previous_recorded_at", pgType: "TIMESTAMPTZ",    swiftModel: "PersonalRecord", swiftProperty: "previousRecordedAt",  swiftType: "Date?"),
        Column(table: "personal_record", pgColumn: "created_at",           pgType: "TIMESTAMPTZ",    swiftModel: "PersonalRecord", swiftProperty: "createdAt",           swiftType: "Date"),
        Column(table: "personal_record", pgColumn: "updated_at",           pgType: "TIMESTAMPTZ",    swiftModel: "PersonalRecord", swiftProperty: "updatedAt",           swiftType: "Date"),

        // MARK: - job
        // user_id, created_at, started_at, completed_at are [BE] — omitted intentionally.

        Column(table: "job", pgColumn: "id",            pgType: "UUID",       swiftModel: "Job", swiftProperty: "id",           swiftType: "UUID"),
        Column(table: "job", pgColumn: "job_type",      pgType: "job_type",   swiftModel: "Job", swiftProperty: "jobType",      swiftType: "JobType"),
        Column(table: "job", pgColumn: "status",        pgType: "job_status", swiftModel: "Job", swiftProperty: "status",       swiftType: "JobStatus"),
        Column(table: "job", pgColumn: "result",        pgType: "JSONB",      swiftModel: "Job", swiftProperty: "result",       swiftType: "String?"),
        Column(table: "job", pgColumn: "error_message", pgType: "TEXT",       swiftModel: "Job", swiftProperty: "errorMessage", swiftType: "String?"),
        Column(table: "job", pgColumn: "expires_at",    pgType: "TIMESTAMPTZ", swiftModel: "Job", swiftProperty: "expiresAt",   swiftType: "Date"),

        // MARK: - sync_event_log

        Column(table: "sync_event_log", pgColumn: "id",          pgType: "UUID",             swiftModel: "SyncEventLog", swiftProperty: "id",          swiftType: "UUID"),
        Column(table: "sync_event_log", pgColumn: "user_id",     pgType: "UUID",             swiftModel: "SyncEventLog", swiftProperty: "user",        swiftType: "User?"),
        Column(table: "sync_event_log", pgColumn: "event_type",  pgType: "sync_event_type",  swiftModel: "SyncEventLog", swiftProperty: "eventType",   swiftType: "SyncEventType"),
        Column(table: "sync_event_log", pgColumn: "entity_type", pgType: "sync_entity_type", swiftModel: "SyncEventLog", swiftProperty: "entityType",  swiftType: "SyncEntityType"),
        Column(table: "sync_event_log", pgColumn: "entity_id",   pgType: "UUID",             swiftModel: "SyncEventLog", swiftProperty: "entityID",    swiftType: "UUID"),
        Column(table: "sync_event_log", pgColumn: "detail",      pgType: "TEXT",             swiftModel: "SyncEventLog", swiftProperty: "detail",      swiftType: "String?"),
        Column(table: "sync_event_log", pgColumn: "occurred_at", pgType: "TIMESTAMPTZ",      swiftModel: "SyncEventLog", swiftProperty: "occurredAt",  swiftType: "Date"),
        Column(table: "sync_event_log", pgColumn: "uploaded_at", pgType: "TIMESTAMPTZ",      swiftModel: "SyncEventLog", swiftProperty: "uploadedAt",  swiftType: "Date?"),

        // MARK: - support_report
        // created_at is [BE] — omitted intentionally.

        Column(table: "support_report", pgColumn: "id",                pgType: "UUID",      swiftModel: "SupportReport", swiftProperty: "id",               swiftType: "UUID"),
        Column(table: "support_report", pgColumn: "user_id",           pgType: "UUID",      swiftModel: "SupportReport", swiftProperty: "user",             swiftType: "User?"),
        Column(table: "support_report", pgColumn: "device_model",      pgType: "TEXT",      swiftModel: "SupportReport", swiftProperty: "deviceModel",      swiftType: "String"),
        Column(table: "support_report", pgColumn: "ios_version",       pgType: "TEXT",      swiftModel: "SupportReport", swiftProperty: "iosVersion",       swiftType: "String"),
        Column(table: "support_report", pgColumn: "app_version",       pgType: "TEXT",      swiftModel: "SupportReport", swiftProperty: "appVersion",       swiftType: "String"),
        // 'description' is reserved by @Model (CustomStringConvertible) — mapped to reportDescription.
        Column(table: "support_report", pgColumn: "description",       pgType: "TEXT",      swiftModel: "SupportReport", swiftProperty: "reportDescription", swiftType: "String"),
        Column(table: "support_report", pgColumn: "sync_log_uploaded", pgType: "BOOLEAN",   swiftModel: "SupportReport", swiftProperty: "syncLogUploaded",  swiftType: "Bool"),
    ]
}
