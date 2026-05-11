import Foundation
@testable import PRLiftsCore
import PRLiftsCoreTestSupport
import SwiftData
import XCTest

@MainActor
final class SupportReportModelTests: XCTestCase {
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

    func testDefaultSyncLogUploaded() throws {
        let report = SupportReport(
            deviceModel: "iPhone 16",
            iosVersion: "18.0",
            appVersion: "1.0.0",
            reportDescription: "Test issue"
        )
        context.insert(report)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SupportReport>())
        XCTAssertFalse(try XCTUnwrap(fetched.first).syncLogUploaded)
    }

    func testFieldsPersist() throws {
        let report = SupportReport.stub()
        context.insert(report)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SupportReport>())
        let result = try XCTUnwrap(fetched.first)

        XCTAssertEqual(result.deviceModel, "iPhone SE (3rd generation)")
        XCTAssertEqual(result.iosVersion, "18.0")
        XCTAssertEqual(result.appVersion, "1.0.0")
        XCTAssertEqual(result.reportDescription, "App crashed on workout screen")
        XCTAssertFalse(result.syncLogUploaded)
    }

    func testSyncLogUploadedToggle() throws {
        let report = SupportReport.stub(syncLogUploaded: true)
        context.insert(report)
        try context.save()

        let fetched = try context.fetch(FetchDescriptor<SupportReport>())
        XCTAssertTrue(try XCTUnwrap(fetched.first).syncLogUploaded)
    }

    func testUserRelationship() throws {
        let user = User.stub()
        let report = SupportReport.stub()
        context.insert(user)
        context.insert(report)
        user.supportReports.append(report)
        try context.save()

        let fetchedUsers = try context.fetch(FetchDescriptor<User>())
        let result = try XCTUnwrap(fetchedUsers.first)

        XCTAssertEqual(result.supportReports.count, 1)
        XCTAssertEqual(result.supportReports.first?.deviceModel, "iPhone SE (3rd generation)")
    }

    func testCascadeDeleteOnUserDelete() throws {
        let user = User.stub()
        let report = SupportReport.stub()
        context.insert(user)
        context.insert(report)
        user.supportReports.append(report)
        try context.save()

        context.delete(user)
        try context.save()

        let reports = try context.fetch(FetchDescriptor<SupportReport>())
        XCTAssertTrue(reports.isEmpty)
    }
}
