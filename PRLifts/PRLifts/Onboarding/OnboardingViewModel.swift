import SwiftUI
import PRLiftsCore

@MainActor
@Observable
final class OnboardingViewModel {
    var email: String = ""
    var displayName: String = ""
    var selectedWeightUnit: WeightUnit
    var selectedMeasurementUnit: MeasurementUnit
    var isLoading: Bool = false
    var errorMessage: String?

    var isDisplayNameValid: Bool {
        !displayName.trimmingCharacters(in: .whitespaces).isEmpty && displayName.count <= 50
    }

    var emailContinueEnabled: Bool {
        !email.trimmingCharacters(in: .whitespaces).isEmpty
    }

    private let authService: any AuthServiceProtocol
    private let profileService: any UserProfileServiceProtocol

    nonisolated init(
        authService: any AuthServiceProtocol = StubAuthService(),
        profileService: any UserProfileServiceProtocol = StubUserProfileService()
    ) {
        self.authService = authService
        self.profileService = profileService
        let isMetric = Locale.current.measurementSystem == .metric
        self.selectedWeightUnit = isMetric ? .kg : .lbs
        self.selectedMeasurementUnit = isMetric ? .cm : .inches
    }

    func prefillDisplayName(from authResult: AuthResult) {
        if let name = authResult.displayName, !name.isEmpty {
            displayName = String(name.prefix(50))
        }
        if let emailValue = authResult.email, email.isEmpty {
            email = emailValue
        }
    }

    func signInWithApple() async -> AuthResult? {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            let result = try await authService.signInWithApple()
            prefillDisplayName(from: result)
            return result
        } catch let error as AuthError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = AuthError.appleSignInFailed.errorDescription
        }
        return nil
    }

    func signInWithGoogle() async -> AuthResult? {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            let result = try await authService.signInWithGoogle()
            prefillDisplayName(from: result)
            return result
        } catch let error as AuthError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = AuthError.googleSignInFailed.errorDescription
        }
        return nil
    }

    func continueWithEmail() async -> AuthResult? {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            let result = try await authService.signInWithEmail(email)
            prefillDisplayName(from: result)
            return result
        } catch let error as AuthError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = AuthError.emailSignInFailed.errorDescription
        }
        return nil
    }

    func saveProfile() async -> Bool {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            try await profileService.createProfile(
                displayName: displayName.trimmingCharacters(in: .whitespaces),
                weightUnit: selectedWeightUnit,
                measurementUnit: selectedMeasurementUnit
            )
            return true
        } catch let error as UserProfileError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = UserProfileError.serverError.errorDescription
        }
        return false
    }
}
