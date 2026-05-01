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

    func testHomeScreen_streakCard_isPresent() {
        XCTAssertTrue(app.staticTexts["0-day streak"].waitForExistence(timeout: 3))
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

    func testHomeScreen_tabSwitch_profileShowsPlaceholder() {
        app.tabBars.buttons["Profile"].tap()
        XCTAssertTrue(app.staticTexts["Profile"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_tabSwitch_returnToHome_showsWordmark() {
        app.tabBars.buttons["History"].tap()
        app.tabBars.buttons["Home"].tap()
        XCTAssertTrue(app.staticTexts["PRLifts"].waitForExistence(timeout: 3))
    }

    // MARK: Start Workout interaction

    func testHomeScreen_startWorkoutButton_showsComingSoonAlert() {
        app.buttons["Start Workout"].tap()
        XCTAssertTrue(app.alerts["Coming Soon"].waitForExistence(timeout: 3))
    }

    func testHomeScreen_comingSoonAlert_dismissesOnOK() {
        app.buttons["Start Workout"].tap()
        XCTAssertTrue(app.alerts["Coming Soon"].waitForExistence(timeout: 3))
        app.alerts["Coming Soon"].buttons["OK"].tap()
        XCTAssertFalse(app.alerts["Coming Soon"].exists)
    }
}
