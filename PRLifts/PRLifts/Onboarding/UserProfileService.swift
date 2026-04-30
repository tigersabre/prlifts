import Foundation
import PRLiftsCore

enum UserProfileError: LocalizedError {
    case networkUnavailable
    case serverError

    var errorDescription: String? {
        switch self {
        case .networkUnavailable: return "No internet connection. Check your settings."
        case .serverError: return "Could not save profile. Please try again."
        }
    }
}

protocol UserProfileServiceProtocol: Sendable {
    func createProfile(
        displayName: String,
        weightUnit: WeightUnit,
        measurementUnit: MeasurementUnit
    ) async throws
}

// Stub until backend POST /v1/users endpoint is wired in.
final class StubUserProfileService: UserProfileServiceProtocol {
    nonisolated init() {}

    func createProfile(
        displayName: String,
        weightUnit: WeightUnit,
        measurementUnit: MeasurementUnit
    ) async throws {
        try await Task.sleep(nanoseconds: 800_000_000)
    }
}
