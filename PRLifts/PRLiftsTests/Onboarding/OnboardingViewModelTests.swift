import XCTest
import PRLiftsCore
@testable import PRLifts

// MARK: - Fakes

private final class FakeAuthService: AuthServiceProtocol, @unchecked Sendable {
    var resultToReturn: AuthResult?
    var errorToThrow: AuthError?

    func signInWithApple() async throws -> AuthResult {
        if let error = errorToThrow { throw error }
        return resultToReturn ?? AuthResult(userId: "test-uid", displayName: nil, email: nil)
    }

    func signInWithGoogle() async throws -> AuthResult {
        if let error = errorToThrow { throw error }
        return resultToReturn ?? AuthResult(userId: "test-uid", displayName: nil, email: nil)
    }

    func signInWithEmail(_ email: String) async throws -> AuthResult {
        if let error = errorToThrow { throw error }
        return resultToReturn ?? AuthResult(userId: "test-uid", displayName: nil, email: email)
    }
}

private final class FakeProfileService: UserProfileServiceProtocol, @unchecked Sendable {
    var errorToThrow: UserProfileError?

    func createProfile(
        displayName: String,
        weightUnit: WeightUnit,
        measurementUnit: MeasurementUnit
    ) async throws {
        if let error = errorToThrow { throw error }
    }
}

// MARK: - Tests

@MainActor
final class OnboardingViewModelTests: XCTestCase {
    private var authService: FakeAuthService!
    private var profileService: FakeProfileService!
    private var sut: OnboardingViewModel!

    override func setUp() {
        super.setUp()
        authService = FakeAuthService()
        profileService = FakeProfileService()
        sut = OnboardingViewModel(authService: authService, profileService: profileService)
    }

    // MARK: Display name validation

    func testDisplayNameValid_whenNonEmpty() {
        sut.displayName = "Sarosh"
        XCTAssertTrue(sut.isDisplayNameValid)
    }

    func testDisplayNameInvalid_whenEmpty() {
        sut.displayName = ""
        XCTAssertFalse(sut.isDisplayNameValid)
    }

    func testDisplayNameInvalid_whenWhitespaceOnly() {
        sut.displayName = "   "
        XCTAssertFalse(sut.isDisplayNameValid)
    }

    func testDisplayNameValid_atExactly50Chars() {
        sut.displayName = String(repeating: "a", count: 50)
        XCTAssertTrue(sut.isDisplayNameValid)
    }

    func testDisplayNameInvalid_at51Chars() {
        sut.displayName = String(repeating: "a", count: 51)
        XCTAssertFalse(sut.isDisplayNameValid)
    }

    // MARK: Email continue enabled

    func testEmailContinueEnabled_whenNonEmpty() {
        sut.email = "test@example.com"
        XCTAssertTrue(sut.emailContinueEnabled)
    }

    func testEmailContinueDisabled_whenEmpty() {
        sut.email = ""
        XCTAssertFalse(sut.emailContinueEnabled)
    }

    func testEmailContinueDisabled_whenWhitespaceOnly() {
        sut.email = "   "
        XCTAssertFalse(sut.emailContinueEnabled)
    }

    // MARK: Display name prefill

    func testPrefillDisplayName_fromAuthResult() {
        let result = AuthResult(userId: "u1", displayName: "Jane", email: "jane@example.com")
        sut.prefillDisplayName(from: result)
        XCTAssertEqual(sut.displayName, "Jane")
    }

    func testPrefillDisplayName_truncatesAtMaxLength() {
        let longName = String(repeating: "a", count: 60)
        let result = AuthResult(userId: "u1", displayName: longName, email: nil)
        sut.prefillDisplayName(from: result)
        XCTAssertEqual(sut.displayName.count, 50)
    }

    func testPrefillDisplayName_doesNotOverwriteExisting() {
        sut.displayName = "Existing"
        let result = AuthResult(userId: "u1", displayName: "New", email: nil)
        sut.prefillDisplayName(from: result)
        XCTAssertEqual(sut.displayName, "New")
    }

    func testPrefillEmail_fromAuthResult_whenEmailEmpty() {
        let result = AuthResult(userId: "u1", displayName: nil, email: "test@example.com")
        sut.prefillDisplayName(from: result)
        XCTAssertEqual(sut.email, "test@example.com")
    }

    // MARK: Unit preference defaults

    func testDefaultUnitSelection_matchesLocale() {
        let isMetric = Locale.current.measurementSystem == .metric
        if isMetric {
            XCTAssertEqual(sut.selectedWeightUnit, .kg)
            XCTAssertEqual(sut.selectedMeasurementUnit, .cm)
        } else {
            XCTAssertEqual(sut.selectedWeightUnit, .lbs)
            XCTAssertEqual(sut.selectedMeasurementUnit, .inches)
        }
    }

    func testUnitSelection_canBeChanged() {
        sut.selectedWeightUnit = .kg
        XCTAssertEqual(sut.selectedWeightUnit, .kg)
        sut.selectedWeightUnit = .lbs
        XCTAssertEqual(sut.selectedWeightUnit, .lbs)
    }

    // MARK: Sign in with Apple

    func testSignInWithApple_success_returnsResult() async {
        let result = await sut.signInWithApple()
        XCTAssertNotNil(result)
        XCTAssertNil(sut.errorMessage)
        XCTAssertFalse(sut.isLoading)
    }

    func testSignInWithApple_failure_setsErrorMessage() async {
        authService.errorToThrow = .appleSignInFailed
        let result = await sut.signInWithApple()
        XCTAssertNil(result)
        XCTAssertNotNil(sut.errorMessage)
        XCTAssertFalse(sut.isLoading)
    }

    func testSignInWithApple_networkError_setsErrorMessage() async {
        authService.errorToThrow = .networkUnavailable
        let result = await sut.signInWithApple()
        XCTAssertNil(result)
        XCTAssertEqual(sut.errorMessage, AuthError.networkUnavailable.errorDescription)
    }

    // MARK: Sign in with email

    func testContinueWithEmail_success_returnsResult() async {
        sut.email = "test@example.com"
        let result = await sut.continueWithEmail()
        XCTAssertNotNil(result)
        XCTAssertNil(sut.errorMessage)
    }

    func testContinueWithEmail_failure_setsErrorMessage() async {
        authService.errorToThrow = .emailSignInFailed
        sut.email = "test@example.com"
        let result = await sut.continueWithEmail()
        XCTAssertNil(result)
        XCTAssertNotNil(sut.errorMessage)
    }

    // MARK: Save profile

    func testSaveProfile_success_returnsTrue() async {
        sut.displayName = "Sarosh"
        let success = await sut.saveProfile()
        XCTAssertTrue(success)
        XCTAssertNil(sut.errorMessage)
    }

    func testSaveProfile_failure_returnsFalse() async {
        profileService.errorToThrow = .serverError
        sut.displayName = "Sarosh"
        let success = await sut.saveProfile()
        XCTAssertFalse(success)
        XCTAssertNotNil(sut.errorMessage)
    }

    func testSaveProfile_networkError_setsErrorMessage() async {
        profileService.errorToThrow = .networkUnavailable
        sut.displayName = "Sarosh"
        let success = await sut.saveProfile()
        XCTAssertFalse(success)
        XCTAssertEqual(sut.errorMessage, UserProfileError.networkUnavailable.errorDescription)
    }

    func testIsLoading_falseAfterCompletion() async {
        _ = await sut.saveProfile()
        XCTAssertFalse(sut.isLoading)
    }
}
