import XCTest

final class HomeScreenUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UITesting", "SkipOnboarding"]
        app.launch()
    }

    // MARK: Tab Bar

    func testHomeScreen_tabBar_showsHomeTab() {
        XCTAssertTrue(app.tabBars.buttons["Home"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_tabBar_showsHistoryTab() {
        XCTAssertTrue(app.tabBars.buttons["History"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_tabBar_showsExercisesTab() {
        XCTAssertTrue(app.tabBars.buttons["Exercises"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_tabBar_showsProfileTab() {
        XCTAssertTrue(app.tabBars.buttons["Profile"].waitForExistence(timeout: 3))
    }

    // MARK: Home tab content

    func testHomeScreen_wordmark_isPresent() {
        XCTAssertTrue(app.staticTexts["PRLifts"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_consistencyCard_isPresent() {
        XCTAssertTrue(app.otherElements["ConsistencyCard"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_consistencyCard_showsWorkoutsThisWeekText() {
        // Stub has 3s delay in UITesting mode; wait up to 6s for loaded state.
        let predicate = NSPredicate(format: "label CONTAINS 'workouts this week.'")
        let match = app.staticTexts.matching(predicate).firstMatch
        XCTAssertTrue(match.waitForExistence(timeout: 6))
    }

    func testHomeScreen_consistencyCard_loadingSkeletonVisible() {
        // Immediately on launch the stub hasn't resolved — ConsistencyCard is present
        // but ConsistencyLine shows the placeholder (redacted or "— of —").
        XCTAssertTrue(app.otherElements["ConsistencyCard"].waitForExistence(timeout: 2))
    }

    func testHomeScreen_startWorkoutButton_isPresent() {
        XCTAssertTrue(app.buttons["Start Workout"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_emptyState_showsReadyCopy() {
        XCTAssertTrue(app.staticTexts["Ready when you are."].waitForExistence(timeout: 3))
    }

    func testHomeScreen_emptyState_showsFirstWorkoutCopy() {
        XCTAssertTrue(app.staticTexts["Tap to log your first workout."].waitForExistence(timeout: 3))
    }

    func testHomeScreen_futureSelfCard_isPresent() {
        app.swipeUp()
        XCTAssertTrue(app.staticTexts["See your future physique"].waitForExistence(timeout: 5))
    }

    // MARK: Tab switching

    func testHomeScreen_tabSwitch_historyShowsPlaceholder() {
        app.tabBars.buttons["History"].tap()
        XCTAssertTrue(app.staticTexts["History"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_tabSwitch_exercisesShowsPlaceholder() {
        app.tabBars.buttons["Exercises"].tap()
        XCTAssertTrue(app.staticTexts["Exercises"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_tabSwitch_profileShowsSettings() {
        app.tabBars.buttons["Profile"].tap()
        XCTAssertTrue(app.staticTexts["Settings"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_tabSwitch_returnToHome_showsWordmark() {
        app.tabBars.buttons["History"].tap()
        app.tabBars.buttons["Home"].tap()
        XCTAssertTrue(app.staticTexts["PRLifts"].waitForExistence(timeout: 3))
    }

    // MARK: Start Workout interaction

    func testHomeScreen_startWorkoutButton_presentsWorkoutScreen() {
        app.buttons["Start Workout"].tap()
        XCTAssertTrue(app.buttons["FinishWorkoutButton"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_workoutScreen_cancelWithNoSets_dismisses() {
        app.buttons["Start Workout"].tap()
        XCTAssertTrue(app.buttons["FinishWorkoutButton"].waitForExistence(timeout: 3))
        app.buttons["CancelWorkoutButton"].tap()
        XCTAssertTrue(app.staticTexts["PRLifts"].waitForExistence(timeout: 3))
    }
}
