import XCTest

final class WorkoutScreenUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UITesting", "SkipOnboarding"]
        app.launch()
    }

    private func openWorkoutScreen() {
        app.buttons["Start Workout"].tap()
        XCTAssertTrue(app.buttons["FinishWorkoutButton"].waitForExistence(timeout: 3))
    }

    // MARK: Presentation

    func testWorkoutScreen_isPresented_whenStartWorkoutTapped() {
        openWorkoutScreen()
        XCTAssertTrue(app.buttons["FinishWorkoutButton"].exists)
    }

    func testWorkoutScreen_showsTimer() {
        openWorkoutScreen()
        XCTAssertTrue(
            app.staticTexts.matching(identifier: "WorkoutTimer").firstMatch.waitForExistence(timeout: 3)
        )
    }

    func testWorkoutScreen_showsAddExerciseButton() {
        openWorkoutScreen()
        XCTAssertTrue(app.buttons["AddExerciseButton"].waitForExistence(timeout: 3))
    }

    // MARK: Cancel

    func testWorkoutScreen_cancelWithNoSets_dismisses() {
        openWorkoutScreen()
        app.buttons["CancelWorkoutButton"].tap()
        XCTAssertTrue(app.staticTexts["PRLifts"].waitForExistence(timeout: 3))
    }

    // MARK: Add Exercise

    func testWorkoutScreen_addExercise_showsPicker() {
        openWorkoutScreen()
        app.buttons["AddExerciseButton"].tap()
        XCTAssertTrue(app.staticTexts["Add Exercise"].waitForExistence(timeout: 3))
    }

    // MARK: Finish with no sets

    func testWorkoutScreen_finishWithNoSets_showsConfirmationDialog() {
        openWorkoutScreen()
        app.buttons["FinishWorkoutButton"].tap()
        XCTAssertTrue(app.sheets.staticTexts["No sets logged"].waitForExistence(timeout: 3))
    }

    func testWorkoutScreen_finishWithNoSets_discardReturnsHome() {
        openWorkoutScreen()
        app.buttons["FinishWorkoutButton"].tap()
        XCTAssertTrue(app.sheets.buttons["Discard Workout"].waitForExistence(timeout: 3))
        app.sheets.buttons["Discard Workout"].tap()
        XCTAssertTrue(app.staticTexts["PRLifts"].waitForExistence(timeout: 3))
    }
}
