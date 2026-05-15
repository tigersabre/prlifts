import XCTest

final class InsightCardUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UITesting", "SkipOnboarding"]
        app.launch()
    }

    // Opens workout, adds an exercise, logs a set, and finishes.
    // Waits for sync to complete (WorkoutSummaryScreen shows "Workout complete!").
    private func completeWorkout() {
        app.buttons["Start Workout"].tap()
        XCTAssertTrue(app.buttons["FinishWorkoutButton"].waitForExistence(timeout: 3))

        app.buttons["AddExerciseButton"].tap()
        XCTAssertTrue(app.staticTexts["Add Exercise"].waitForExistence(timeout: 3))

        let searchField = app.searchFields.firstMatch
        XCTAssertTrue(searchField.waitForExistence(timeout: 3))
        searchField.tap()
        searchField.typeText("Bench")

        let benchRow = app.staticTexts["Bench Press"].firstMatch
        XCTAssertTrue(benchRow.waitForExistence(timeout: 5))
        benchRow.tap()

        let repsField = app.textFields["RepsInput"]
        XCTAssertTrue(repsField.waitForExistence(timeout: 3))
        repsField.tap()
        repsField.typeText("5")
        app.buttons["LogSetButton"].tap()

        app.buttons["FinishWorkoutButton"].tap()

        // Wait for PR sync (4s stub) + summary heading to appear
        XCTAssertTrue(
            app.staticTexts.matching(identifier: "WorkoutCompleteHeading").firstMatch
                .waitForExistence(timeout: 10)
        )
    }

    // MARK: Card presence

    func testInsightCard_headerAppearsAfterSyncCompletes() {
        completeWorkout()
        // PR sync stub takes 4s in UITesting mode, then insight is triggered.
        // InsightCardHeader appears as soon as insight trigger fires.
        XCTAssertTrue(
            app.staticTexts.matching(identifier: "InsightCardHeader").firstMatch
                .waitForExistence(timeout: 10)
        )
    }

    // MARK: Loading state

    func testInsightCard_showsLoadingText_duringRequest() {
        completeWorkout()
        // InsightLoadingText is visible during the 3s stub poll delay (UITesting mode)
        XCTAssertTrue(
            app.staticTexts.matching(identifier: "InsightLoadingText").firstMatch
                .waitForExistence(timeout: 10)
        )
    }

    // MARK: Success state

    func testInsightCard_showsInsightText_afterSuccess() {
        completeWorkout()
        // Stub total delay in UITesting: 500ms request + 3s poll = ~3.5s after sync.
        // Overall timeout from completeWorkout: 10s for sync + 10s here = plenty.
        XCTAssertTrue(
            app.staticTexts.matching(identifier: "InsightText").firstMatch
                .waitForExistence(timeout: 15)
        )
    }
}
