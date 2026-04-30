import Foundation
import SwiftData

@Model
public final class PersonalRecord {
    public var id: UUID
    public var weightModifier: WeightModifier
    public var recordType: RecordType
    public var value: Double
    public var valueUnit: ValueUnit?
    public var recordedAt: Date
    public var previousValue: Double?
    public var previousRecordedAt: Date?
    // Stored as UUID rather than a SwiftData relationship — PR records the triggering set
    // but does not own it. The set can be edited without invalidating the PR record.
    public var workoutSetID: UUID
    public var createdAt: Date
    public var updatedAt: Date

    public var user: User?
    public var exercise: Exercise?

    public init(
        id: UUID = UUID(),
        weightModifier: WeightModifier,
        recordType: RecordType,
        value: Double,
        valueUnit: ValueUnit? = nil,
        recordedAt: Date,
        previousValue: Double? = nil,
        previousRecordedAt: Date? = nil,
        workoutSetID: UUID,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.weightModifier = weightModifier
        self.recordType = recordType
        self.value = value
        self.valueUnit = valueUnit
        self.recordedAt = recordedAt
        self.previousValue = previousValue
        self.previousRecordedAt = previousRecordedAt
        self.workoutSetID = workoutSetID
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}
