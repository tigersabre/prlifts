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
        // On iOS 26, the Cancel button of a confirmationDialog action sheet is not
        // accessible via XCUITest element queries. Tap its screen position directly.
        // On iPhone SE 3rd gen (375×667pt), the Cancel button appears at ~y=0.93.
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.93)).tap()
        XCTAssertFalse(
            app.sheets.staticTexts["Delete Account"].waitForExistence(timeout: 3)
        )
    }
}
