import XCTest

final class WorkoutSummaryUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UITesting", "SkipOnboarding"]
        app.launch()
    }

    // Opens workout screen, adds an exercise via search, logs one set.
    private func openWorkoutAndLogSet() {
        app.buttons["Start Workout"].tap()
        XCTAssertTrue(app.buttons["FinishWorkoutButton"].waitForExistence(timeout: 3))

        app.buttons["AddExerciseButton"].tap()
        XCTAssertTrue(app.staticTexts["Add Exercise"].waitForExistence(timeout: 3))

        let searchField = app.searchFields.firstMatch
        XCTAssertTrue(searchField.waitForExistence(timeout: 3))
        searchField.tap()
        searchField.typeText("Bench")

        // Stub: 400ms debounce + 300ms service delay
        let benchRow = app.staticTexts["Bench Press"].firstMatch
        XCTAssertTrue(benchRow.waitForExistence(timeout: 5))
        benchRow.tap()

        let repsField = app.textFields["RepsInput"]
        XCTAssertTrue(repsField.waitForExistence(timeout: 3))
        repsField.tap()
        repsField.typeText("5")
        app.buttons["LogSetButton"].tap()
    }

    // MARK: Presentation

    func testWorkoutSummary_isPresented_afterFinishingWorkout() {
        openWorkoutAndLogSet()
        app.buttons["FinishWorkoutButton"].tap()
        XCTAssertTrue(
            app.staticTexts.matching(identifier: "WorkoutCompleteHeading").firstMatch
                .waitForExistence(timeout: 5)
        )
    }

    // MARK: Loading state

    func testWorkoutSummary_showsCheckingForPRsState() {
        openWorkoutAndLogSet()
        app.buttons["FinishWorkoutButton"].tap()
        // Stub sync takes 800ms — loading text is visible immediately after finish
        XCTAssertTrue(
            app.staticTexts.matching(identifier: "CheckingPRsText").firstMatch
                .waitForExistence(timeout: 3)
        )
    }

    // MARK: Done

    func testWorkoutSummary_doneButton_dismissesAndReturnsHome() {
        openWorkoutAndLogSet()
        app.buttons["FinishWorkoutButton"].tap()
        XCTAssertTrue(
            app.staticTexts.matching(identifier: "WorkoutCompleteHeading").firstMatch
                .waitForExistence(timeout: 5)
        )
        // Wait for sync to complete (4s stub delay in UI testing mode)
        XCTAssertTrue(app.buttons["SummaryDoneButton"].waitForExistence(timeout: 10))
        app.buttons["SummaryDoneButton"].tap()
        XCTAssertTrue(app.staticTexts["PRLifts"].waitForExistence(timeout: 3))
    }

    // MARK: Stats

    func testWorkoutSummary_showsDurationStat() {
        openWorkoutAndLogSet()
        app.buttons["FinishWorkoutButton"].tap()
        XCTAssertTrue(
            app.staticTexts.matching(identifier: "WorkoutCompleteHeading").firstMatch
                .waitForExistence(timeout: 5)
        )
        XCTAssertTrue(app.staticTexts["Duration"].waitForExistence(timeout: 3))
    }
}
