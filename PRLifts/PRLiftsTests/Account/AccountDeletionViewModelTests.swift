import XCTest
@testable import PRLifts

// MARK: - Fakes

private final class FakeAccountService: AccountServiceProtocol, @unchecked Sendable {
    var errorToThrow: Error?
    private(set) var deleteAccountCallCount = 0

    func deleteAccount() async throws {
        deleteAccountCallCount += 1
        if let error = errorToThrow { throw error }
    }
}

// MARK: - Tests

@MainActor
final class AccountDeletionViewModelTests: XCTestCase {
    private var accountService: FakeAccountService!
    private var sut: AccountDeletionViewModel!

    override func setUp() {
        super.setUp()
        accountService = FakeAccountService()
        sut = AccountDeletionViewModel(accountService: accountService)
    }

    // MARK: requestDeletion / cancelDeletion

    func testRequestDeletion_setsIsShowingConfirmation() {
        sut.requestDeletion()
        XCTAssertTrue(sut.isShowingConfirmation)
    }

    func testCancelDeletion_clearsIsShowingConfirmation() {
        sut.requestDeletion()
        sut.cancelDeletion()
        XCTAssertFalse(sut.isShowingConfirmation)
    }

    // MARK: dismissError

    func testDismissError_resetsPhaseToIdle() async {
        accountService.errorToThrow = AccountServiceError.networkError
        _ = await sut.performDeletion(cancelSync: {}, clearLocalData: {}, clearKeychain: {})
        sut.dismissError()
        XCTAssertNil(sut.errorMessage)
        XCTAssertFalse(sut.isDeleting)
    }

    // MARK: isDeleting / errorMessage computed props

    func testIsDeleting_falseInitially() {
        XCTAssertFalse(sut.isDeleting)
    }

    func testErrorMessage_nilWhenIdle() {
        XCTAssertNil(sut.errorMessage)
    }

    // MARK: performDeletion — success path

    func testPerformDeletion_success_returnsTrue() async {
        let result = await sut.performDeletion(cancelSync: {}, clearLocalData: {}, clearKeychain: {})
        XCTAssertTrue(result)
    }

    func testPerformDeletion_success_phaseIsIdle() async {
        _ = await sut.performDeletion(cancelSync: {}, clearLocalData: {}, clearKeychain: {})
        XCTAssertNil(sut.errorMessage)
        XCTAssertFalse(sut.isDeleting)
    }

    func testPerformDeletion_success_callsDeleteAccount() async {
        _ = await sut.performDeletion(cancelSync: {}, clearLocalData: {}, clearKeychain: {})
        XCTAssertEqual(accountService.deleteAccountCallCount, 1)
    }

    func testPerformDeletion_cancelsSync_beforeApiCall() async {
        var callLog: [String] = []
        accountService.errorToThrow = nil

        _ = await sut.performDeletion(
            cancelSync: { callLog.append("cancelSync") },
            clearLocalData: { callLog.append("clearLocalData") },
            clearKeychain: { callLog.append("clearKeychain") }
        )

        XCTAssertEqual(callLog.first, "cancelSync")
    }

    func testPerformDeletion_clearsLocalData_onSuccess() async {
        var didClearLocalData = false
        _ = await sut.performDeletion(
            cancelSync: {},
            clearLocalData: { didClearLocalData = true },
            clearKeychain: {}
        )
        XCTAssertTrue(didClearLocalData)
    }

    func testPerformDeletion_clearsKeychain_onSuccess() async {
        var didClearKeychain = false
        _ = await sut.performDeletion(
            cancelSync: {},
            clearLocalData: {},
            clearKeychain: { didClearKeychain = true }
        )
        XCTAssertTrue(didClearKeychain)
    }

    func testPerformDeletion_dismissesConfirmation_onStart() async {
        sut.requestDeletion()
        _ = await sut.performDeletion(cancelSync: {}, clearLocalData: {}, clearKeychain: {})
        XCTAssertFalse(sut.isShowingConfirmation)
    }

    // MARK: performDeletion — failure path

    func testPerformDeletion_networkError_returnsFalse() async {
        accountService.errorToThrow = AccountServiceError.networkError
        let result = await sut.performDeletion(cancelSync: {}, clearLocalData: {}, clearKeychain: {})
        XCTAssertFalse(result)
    }

    func testPerformDeletion_serverError_returnsFalse() async {
        accountService.errorToThrow = AccountServiceError.serverError("Deletion failed")
        let result = await sut.performDeletion(cancelSync: {}, clearLocalData: {}, clearKeychain: {})
        XCTAssertFalse(result)
    }

    func testPerformDeletion_networkError_setsErrorMessage() async {
        accountService.errorToThrow = AccountServiceError.networkError
        _ = await sut.performDeletion(cancelSync: {}, clearLocalData: {}, clearKeychain: {})
        XCTAssertNotNil(sut.errorMessage)
    }

    func testPerformDeletion_doesNotClearLocalData_onFailure() async {
        accountService.errorToThrow = AccountServiceError.networkError
        var didClearLocalData = false
        _ = await sut.performDeletion(
            cancelSync: {},
            clearLocalData: { didClearLocalData = true },
            clearKeychain: {}
        )
        XCTAssertFalse(didClearLocalData)
    }

    func testPerformDeletion_doesNotClearKeychain_onFailure() async {
        accountService.errorToThrow = AccountServiceError.networkError
        var didClearKeychain = false
        _ = await sut.performDeletion(
            cancelSync: {},
            clearLocalData: {},
            clearKeychain: { didClearKeychain = true }
        )
        XCTAssertFalse(didClearKeychain)
    }

    func testPerformDeletion_unexpectedError_returnsFalse() async {
        struct UnexpectedError: Error {}
        accountService.errorToThrow = UnexpectedError()
        let result = await sut.performDeletion(cancelSync: {}, clearLocalData: {}, clearKeychain: {})
        XCTAssertFalse(result)
    }

    func testPerformDeletion_unexpectedError_setsGenericErrorMessage() async {
        struct UnexpectedError: Error {}
        accountService.errorToThrow = UnexpectedError()
        _ = await sut.performDeletion(cancelSync: {}, clearLocalData: {}, clearKeychain: {})
        XCTAssertEqual(sut.errorMessage, "Something went wrong. Please try again.")
    }
}
