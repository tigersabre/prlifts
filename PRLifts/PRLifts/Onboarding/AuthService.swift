import Foundation

struct AuthResult {
    let userId: String
    let displayName: String?
    let email: String?
}

enum AuthError: LocalizedError {
    case appleSignInFailed
    case googleSignInFailed
    case emailSignInFailed
    case networkUnavailable
    case unknown

    var errorDescription: String? {
        switch self {
        case .appleSignInFailed:  return "Sign in with Apple failed. Try another method."
        case .googleSignInFailed: return "Sign in with Google failed. Try another method."
        case .emailSignInFailed:  return "Sign in failed. Please try again."
        case .networkUnavailable: return "No internet connection. Check your settings."
        case .unknown:            return "Sign in failed. Please try again."
        }
    }
}

protocol AuthServiceProtocol: Sendable {
    func signInWithApple() async throws -> AuthResult
    func signInWithGoogle() async throws -> AuthResult
    func signInWithEmail(_ email: String) async throws -> AuthResult
}

// Stub used until [INFRA] Configure Sign in with Apple capability is complete.
// Replace with real Supabase Auth implementation when that PR merges.
final class StubAuthService: AuthServiceProtocol {
    nonisolated init() {}

    func signInWithApple() async throws -> AuthResult {
        try await Task.sleep(nanoseconds: 500_000_000)
        return AuthResult(userId: UUID().uuidString, displayName: nil, email: nil)
    }

    func signInWithGoogle() async throws -> AuthResult {
        try await Task.sleep(nanoseconds: 500_000_000)
        return AuthResult(userId: UUID().uuidString, displayName: nil, email: nil)
    }

    func signInWithEmail(_ email: String) async throws -> AuthResult {
        try await Task.sleep(nanoseconds: 500_000_000)
        return AuthResult(userId: UUID().uuidString, displayName: nil, email: email)
    }
}
