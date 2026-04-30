import Foundation
@testable import PRLiftsCore
import XCTest

final class MigrationManagerTests: XCTestCase {
    var testDefaults: UserDefaults!
    let testSuiteName = "com.prlifts.test.migrationmanager"

    override func setUp() {
        super.setUp()
        testDefaults = UserDefaults(suiteName: testSuiteName)
        testDefaults.removePersistentDomain(forName: testSuiteName)
        MigrationManager.userDefaults = testDefaults
    }

    override func tearDown() {
        testDefaults.removePersistentDomain(forName: testSuiteName)
        MigrationManager.userDefaults = .standard
        testDefaults = nil
        super.tearDown()
    }

    func testInitialStateIsNotFailed() {
        XCTAssertFalse(MigrationManager.migrationFailed)
    }

    func testBeginMigrationSetsFlag() {
        MigrationManager.beginMigration()
        XCTAssertTrue(MigrationManager.migrationFailed)
    }

    func testCompleteMigrationClearsFlag() {
        MigrationManager.beginMigration()
        MigrationManager.completeMigration()
        XCTAssertFalse(MigrationManager.migrationFailed)
    }

    func testResetMigrationFlagClearsFlag() {
        MigrationManager.beginMigration()
        MigrationManager.resetMigrationFlag()
        XCTAssertFalse(MigrationManager.migrationFailed)
    }

    func testFlagPersistsWithoutCompletion() {
        MigrationManager.beginMigration()
        // Simulate app relaunch by re-reading from the same UserDefaults
        XCTAssertTrue(MigrationManager.migrationFailed)
    }

    func testMultipleBeginCallsDoNotBreakCompletion() {
        MigrationManager.beginMigration()
        MigrationManager.beginMigration()
        MigrationManager.completeMigration()
        XCTAssertFalse(MigrationManager.migrationFailed)
    }

    func testCompletionWithoutBeginIsNoOp() {
        MigrationManager.completeMigration()
        XCTAssertFalse(MigrationManager.migrationFailed)
    }

    func testCurrentVersionIsPositive() {
        XCTAssertGreaterThan(MigrationManager.currentVersion, 0)
    }

    func testBeginAndCompleteAreSymmetric() {
        XCTAssertFalse(MigrationManager.migrationFailed)
        MigrationManager.beginMigration()
        XCTAssertTrue(MigrationManager.migrationFailed)
        MigrationManager.completeMigration()
        XCTAssertFalse(MigrationManager.migrationFailed)
    }

    func testResetAfterSuccessfulMigrationIsNoOp() {
        MigrationManager.beginMigration()
        MigrationManager.completeMigration()
        MigrationManager.resetMigrationFlag()
        XCTAssertFalse(MigrationManager.migrationFailed)
    }
}
