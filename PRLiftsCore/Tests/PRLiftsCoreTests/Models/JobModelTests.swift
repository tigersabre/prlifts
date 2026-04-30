import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class JobModelTests: XCTestCase {
    var container: ModelContainer!
    var context: ModelContext!

    override func setUp() async throws {
        container = try TestContainerFactory.make()
        context = container.mainContext
    }

    override func tearDown() async throws {
        context = nil
        container = nil
    }

    func testDefaultStatus() throws {
        let job = Job.stub()
        context.insert(job)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        XCTAssertEqual(fetched.first?.status, .pending)
    }

    func testJobTypePersistence() throws {
        for jobType in JobType.allCases {
            let job = Job.stub(jobType: jobType)
            context.insert(job)
        }
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        XCTAssertEqual(fetched.count, JobType.allCases.count)
    }

    func testJobStatusPersistence() throws {
        for status in JobStatus.allCases {
            let job = Job.stub(status: status)
            context.insert(job)
        }
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        XCTAssertEqual(fetched.count, JobStatus.allCases.count)
    }

    func testExpiresAtDefaultIs5MinutesFromNow() {
        let before = Date()
        let job = Job.stub()
        let after = Date()

        let expectedMin = before.addingTimeInterval(300)
        let expectedMax = after.addingTimeInterval(300)

        XCTAssertGreaterThanOrEqual(job.expiresAt, expectedMin)
        XCTAssertLessThanOrEqual(job.expiresAt, expectedMax)
    }

    func testResultPersistence() throws {
        let job = Job.stub()
        job.result = #"{"insight": "Great workout!"}"#
        context.insert(job)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        XCTAssertEqual(fetched.first?.result, #"{"insight": "Great workout!"}"#)
    }

    func testErrorMessagePersistence() throws {
        let job = Job.stub(status: .failed)
        job.errorMessage = "AI provider unavailable"
        context.insert(job)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        XCTAssertEqual(fetched.first?.errorMessage, "AI provider unavailable")
    }

    func testStartedAtPersistence() throws {
        let startedAt = Date()
        let job = Job.stub(status: .processing)
        job.startedAt = startedAt
        context.insert(job)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        let result = try XCTUnwrap(fetched.first?.startedAt)

        XCTAssertEqual(result.timeIntervalSinceReferenceDate, startedAt.timeIntervalSinceReferenceDate, accuracy: 0.001)
    }

    func testCompletedAtPersistence() throws {
        let completedAt = Date()
        let job = Job.stub(status: .complete)
        job.completedAt = completedAt
        context.insert(job)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        let result = try XCTUnwrap(fetched.first?.completedAt)

        XCTAssertEqual(
            result.timeIntervalSinceReferenceDate,
            completedAt.timeIntervalSinceReferenceDate,
            accuracy: 0.001
        )
    }

    func testNilResultAndErrorForPendingJob() throws {
        let job = Job.stub()
        context.insert(job)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        XCTAssertNil(fetched.first?.result)
        XCTAssertNil(fetched.first?.errorMessage)
        XCTAssertNil(fetched.first?.startedAt)
        XCTAssertNil(fetched.first?.completedAt)
    }

    func testInsightJobType() throws {
        let job = Job.stub(jobType: .insight)
        context.insert(job)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        XCTAssertEqual(fetched.first?.jobType, .insight)
    }

    func testFutureSelfJobType() throws {
        let job = Job.stub(jobType: .futureSelf)
        context.insert(job)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        XCTAssertEqual(fetched.first?.jobType, .futureSelf)
    }

    func testExpiredStatusPersistence() throws {
        let job = Job.stub(status: .expired)
        context.insert(job)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<Job>())
        XCTAssertEqual(fetched.first?.status, .expired)
    }
}
