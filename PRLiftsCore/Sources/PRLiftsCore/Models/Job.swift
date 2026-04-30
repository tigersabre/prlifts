import Foundation
import SwiftData

@Model
public final class Job {
    public var id: UUID
    public var jobType: JobType
    public var status: JobStatus
    public var result: String?
    public var errorMessage: String?
    public var startedAt: Date?
    public var completedAt: Date?
    public var expiresAt: Date
    public var createdAt: Date

    public var user: User?

    public init(
        id: UUID = UUID(),
        jobType: JobType,
        status: JobStatus = .pending,
        result: String? = nil,
        errorMessage: String? = nil,
        startedAt: Date? = nil,
        completedAt: Date? = nil,
        expiresAt: Date = Date().addingTimeInterval(300),
        createdAt: Date = Date()
    ) {
        self.id = id
        self.jobType = jobType
        self.status = status
        self.result = result
        self.errorMessage = errorMessage
        self.startedAt = startedAt
        self.completedAt = completedAt
        self.expiresAt = expiresAt
        self.createdAt = createdAt
    }
}
