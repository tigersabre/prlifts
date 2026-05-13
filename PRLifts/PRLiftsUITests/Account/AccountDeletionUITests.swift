import XCTest

final class AccountDeletionUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UITesting", "SkipOnboarding"]
        app.launch()
        app.tabBars.buttons["Profile"].tap()
    }

    // MARK: Settings screen

    func testSettingsScreen_deleteAccountButton_isPresent() {
        XCTAssertTrue(
            app.buttons["Delete Account"].waitForExistence(timeout: 3)
        )
    }

    // MARK: Confirmation dialog

    func testSettingsScreen_deleteAccountButton_showsConfirmationDialog() {
        app.buttons["Delete Account"].tap()
        XCTAssertTrue(
            app.sheets.staticTexts["Delete Account"].waitForExistence(timeout: 3)
        )
    }

    func testSettingsScreen_confirmationDialog_hasDestructiveButton() {
        app.buttons["Delete Account"].tap()
        XCTAssertTrue(
            app.sheets.buttons["Delete My Account"].waitForExistence(timeout: 3)
        )
    }

    func testSettingsScreen_confirmationDialog_cancelDismissesDialog() {
        app.buttons["Delete Account"].tap()
        XCTAssertTrue(app.sheets.staticTexts["Delete Account"].waitForExistence(timeout: 3))
        // On iOS 26, confirmationDialog renders as a popover (sheet frame ~y=445–657).
        // The Cancel button does not appear in the accessibility tree. Dismiss by tapping
        // the PopoverDismissRegion above the sheet (y≈0.3 → ~y=200pt, well above sheet).
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.3)).tap()
        XCTAssertFalse(
            app.sheets.staticTexts["Delete Account"].waitForExistence(timeout: 3)
        )
    }

    func testSettingsScreen_confirmationDialog_cancelKeepsSettingsVisible() {
        app.buttons["Delete Account"].tap()
        XCTAssertTrue(app.sheets.staticTexts["Delete Account"].waitForExistence(timeout: 3))
        // Same coordinate-tap workaround as the dismiss test above.
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.3)).tap()
        // Settings screen and its tab bar remain — no navigation has occurred.
        XCTAssertTrue(app.buttons["Delete Account"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.tabBars.buttons["Profile"].exists)
    }

    // MARK: Confirm flow

    func testSettingsScreen_confirm_navigatesToOnboarding() {
        app.buttons["Delete Account"].tap()
        XCTAssertTrue(app.sheets.buttons["Delete My Account"].waitForExistence(timeout: 3))
        app.sheets.buttons["Delete My Account"].tap()
        // The loading overlay (ProgressView) is transient (~800 ms stub) and not reliably
        // catchable in XCUITest because tap() waits for app-idle, which can happen after
        // the stub completes. isDeleting state is covered by unit test
        // AccountDeletionViewModelTests.testIsDeleting_trueWhileDeleting.
        // After the stub completes, hasCompletedOnboarding = false and the app
        // navigates to onboarding root via @AppStorage reactive binding.
        XCTAssertTrue(app.buttons["Get started"].waitForExistence(timeout: 5))
    }
}
