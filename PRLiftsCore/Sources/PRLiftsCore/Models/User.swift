import Foundation
import SwiftData

@Model
public final class User {
    public var id: UUID
    public var email: String?
    public var displayName: String?
    public var avatarURL: String?
    public var unitPreference: WeightUnit
    public var measurementUnit: MeasurementUnit
    public var dateOfBirth: Date?
    public var gender: Gender
    public var goal: UserGoal?
    public var phase2CompletedAt: Date?
    public var betaTier: BetaTier
    public var createdAt: Date
    public var updatedAt: Date

    @Relationship(deleteRule: .cascade, inverse: \Workout.user)
    public var workouts: [Workout]

    @Relationship(deleteRule: .cascade, inverse: \PersonalRecord.user)
    public var personalRecords: [PersonalRecord]

    @Relationship(deleteRule: .cascade, inverse: \Job.user)
    public var jobs: [Job]

    @Relationship(deleteRule: .cascade, inverse: \SyncEventLog.user)
    public var syncEventLogs: [SyncEventLog]

    @Relationship(deleteRule: .cascade, inverse: \SupportReport.user)
    public var supportReports: [SupportReport]

    public init(
        id: UUID = UUID(),
        email: String? = nil,
        displayName: String? = nil,
        avatarURL: String? = nil,
        unitPreference: WeightUnit = .lbs,
        measurementUnit: MeasurementUnit = .cm,
        dateOfBirth: Date? = nil,
        gender: Gender = .na,
        goal: UserGoal? = nil,
        phase2CompletedAt: Date? = nil,
        betaTier: BetaTier = .none,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.email = email
        self.displayName = displayName
        self.avatarURL = avatarURL
        self.unitPreference = unitPreference
        self.measurementUnit = measurementUnit
        self.dateOfBirth = dateOfBirth
        self.gender = gender
        self.goal = goal
        self.phase2CompletedAt = phase2CompletedAt
        self.betaTier = betaTier
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.workouts = []
        self.personalRecords = []
        self.jobs = []
        self.syncEventLogs = []
        self.supportReports = []
    }
}
