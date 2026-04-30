import XCTest

final class OnboardingUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UITesting", "ResetOnboarding"]
        app.launch()
    }

    // MARK: - WelcomeScreen

    func testWelcomeScreen_hasWordmark() {
        XCTAssertTrue(app.staticTexts["PRLifts"].waitForExistence(timeout: 3))
    }

    func testWelcomeScreen_hasGetStartedButton() {
        XCTAssertTrue(app.buttons["Get started"].waitForExistence(timeout: 3))
    }

    func testWelcomeScreen_hasSignInLink() {
        XCTAssertTrue(app.buttons["Sign in to existing account"].waitForExistence(timeout: 3))
    }

    func testWelcomeScreen_getStarted_navigatesToSignIn() {
        app.buttons["Get started"].tap()
        XCTAssertTrue(app.staticTexts["Sign in to PRLifts"].waitForExistence(timeout: 3))
    }

    // MARK: - SignInScreen

    func testSignInScreen_hasAppleButton() {
        app.buttons["Get started"].tap()
        XCTAssertTrue(app.buttons["Sign in with Apple"].waitForExistence(timeout: 3))
    }

    func testSignInScreen_hasGoogleButton() {
        app.buttons["Get started"].tap()
        XCTAssertTrue(app.buttons["Sign in with Google"].waitForExistence(timeout: 3))
    }

    func testSignInScreen_hasEmailField() {
        app.buttons["Get started"].tap()
        XCTAssertTrue(app.textFields["Email address"].waitForExistence(timeout: 3))
    }

    func testSignInScreen_continueButton_disabledWithEmptyEmail() {
        app.buttons["Get started"].tap()
        let continueButton = app.buttons["Continue"]
        XCTAssertTrue(continueButton.waitForExistence(timeout: 3))
        XCTAssertFalse(continueButton.isEnabled)
    }

    func testSignInScreen_emailEntry_enablesContinue() {
        app.buttons["Get started"].tap()
        let emailField = app.textFields["Email address"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 3))
        emailField.tap()
        emailField.typeText("test@example.com")
        let continueButton = app.buttons["Continue"]
        XCTAssertTrue(continueButton.isEnabled)
    }

    func testSignInScreen_emailContinue_navigatesToDisplayName() {
        app.buttons["Get started"].tap()
        let emailField = app.textFields["Email address"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 3))
        emailField.tap()
        emailField.typeText("test@example.com")
        app.buttons["Continue"].tap()
        XCTAssertTrue(app.staticTexts["What should we\ncall you?"].waitForExistence(timeout: 5))
    }

    // MARK: - DisplayNameScreen

    func testDisplayNameScreen_hasContinueDisabledInitially() {
        navigateToDisplayName()
        let continueButton = app.buttons["Continue"]
        XCTAssertTrue(continueButton.waitForExistence(timeout: 3))
        XCTAssertFalse(continueButton.isEnabled)
    }

    func testDisplayNameScreen_validInput_enablesContinue() {
        navigateToDisplayName()
        let field = app.textFields["Display name, 0 of 50 characters"]
        XCTAssertTrue(field.waitForExistence(timeout: 3))
        field.tap()
        field.typeText("Sarosh")
        XCTAssertTrue(app.buttons["Continue"].isEnabled)
    }

    func testDisplayNameScreen_backButton_returnsToSignIn() {
        navigateToDisplayName()
        app.buttons["Back"].tap()
        XCTAssertTrue(app.staticTexts["Sign in to PRLifts"].waitForExistence(timeout: 3))
    }

    // MARK: - UnitPreferenceScreen

    func testUnitPreferenceScreen_hasBothWeightCards() {
        navigateToUnitPreference()
        XCTAssertTrue(app.buttons["lbs, Pounds"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.buttons["kg, Kilograms"].waitForExistence(timeout: 3))
    }

    func testUnitPreferenceScreen_hasBothHeightCards() {
        navigateToUnitPreference()
        XCTAssertTrue(app.buttons["in, Inches"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.buttons["cm, Centimeters"].waitForExistence(timeout: 3))
    }

    func testUnitPreferenceScreen_hasStartTrackingButton() {
        navigateToUnitPreference()
        XCTAssertTrue(app.buttons["Start tracking"].waitForExistence(timeout: 3))
    }

    func testUnitPreferenceScreen_backButton_returnsToDisplayName() {
        navigateToUnitPreference()
        app.buttons["Back"].tap()
        XCTAssertTrue(app.staticTexts["What should we\ncall you?"].waitForExistence(timeout: 3))
    }

    func testUnitPreferenceScreen_weightCardSelection_toggling() {
        navigateToUnitPreference()
        let kgCard = app.buttons["kg, Kilograms"]
        XCTAssertTrue(kgCard.waitForExistence(timeout: 3))
        kgCard.tap()
        XCTAssertTrue(kgCard.isSelected)
    }

    // MARK: - Happy path (end-to-end)

    func testHappyPath_welcome_through_unitPreference() {
        app.buttons["Get started"].tap()

        let emailField = app.textFields["Email address"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 3))
        emailField.tap()
        emailField.typeText("test@example.com")
        app.buttons["Continue"].tap()

        let nameField = app.textFields["Display name, 0 of 50 characters"]
        XCTAssertTrue(nameField.waitForExistence(timeout: 5))
        nameField.tap()
        nameField.typeText("Sarosh")
        app.buttons["Continue"].tap()

        XCTAssertTrue(app.buttons["Start tracking"].waitForExistence(timeout: 5))
        app.buttons["Start tracking"].tap()

        XCTAssertTrue(app.staticTexts["PRLifts"].waitForExistence(timeout: 5))
    }

    // MARK: - Helpers

    private func navigateToDisplayName() {
        app.buttons["Get started"].tap()
        let emailField = app.textFields["Email address"]
        guard emailField.waitForExistence(timeout: 3) else { return }
        emailField.tap()
        emailField.typeText("test@example.com")
        app.buttons["Continue"].tap()
    }

    private func navigateToUnitPreference() {
        navigateToDisplayName()
        let field = app.textFields["Display name, 0 of 50 characters"]
        guard field.waitForExistence(timeout: 5) else { return }
        field.tap()
        field.typeText("Sarosh")
        app.buttons["Continue"].tap()
    }
}
