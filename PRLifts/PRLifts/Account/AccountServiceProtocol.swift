import Foundation

enum AccountServiceError: LocalizedError {
    case networkError
    case serverError(String)

    var errorDescription: String? {
        switch self {
        case .networkError:
            return "No internet connection. Check your settings."
        case .serverError(let msg):
            return msg.isEmpty ? "Something went wrong. Please try again." : msg
        }
    }
}

protocol AccountServiceProtocol: Sendable {
    func deleteAccount() async throws
}

// Stub used until real URLSession-backed implementation is wired.
final class StubAccountService: AccountServiceProtocol {
    nonisolated init() {}

    func deleteAccount() async throws {
        try await Task.sleep(for: .milliseconds(800))
    }
}
