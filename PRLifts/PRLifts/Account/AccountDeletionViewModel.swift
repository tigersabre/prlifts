import Foundation

@MainActor
@Observable
final class AccountDeletionViewModel {
    enum Phase {
        case idle
        case deleting
        case failed(String)
    }

    var phase: Phase = .idle
    var isShowingConfirmation = false

    private let accountService: any AccountServiceProtocol

    nonisolated init(accountService: any AccountServiceProtocol = StubAccountService()) {
        self.accountService = accountService
    }

    var isDeleting: Bool {
        if case .deleting = phase { return true }
        return false
    }

    var errorMessage: String? {
        if case .failed(let msg) = phase { return msg }
        return nil
    }

    func requestDeletion() {
        isShowingConfirmation = true
    }

    func cancelDeletion() {
        isShowingConfirmation = false
    }

    func dismissError() {
        phase = .idle
    }

    /// Executes the full deletion cascade. Returns true on success; on failure
    /// sets phase to .failed and returns false without touching local data.
    func performDeletion(
        cancelSync: () -> Void,
        clearLocalData: () async throws -> Void,
        clearKeychain: () -> Void
    ) async -> Bool {
        isShowingConfirmation = false
        phase = .deleting
        cancelSync()
        do {
            try await accountService.deleteAccount()
        } catch let error as AccountServiceError {
            phase = .failed(error.errorDescription ?? "Something went wrong. Please try again.")
            return false
        } catch {
            phase = .failed("Something went wrong. Please try again.")
            return false
        }
        try? await clearLocalData()
        clearKeychain()
        phase = .idle
        return true
    }
}
