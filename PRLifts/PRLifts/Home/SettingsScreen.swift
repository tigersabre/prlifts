import SwiftUI
import SwiftData
import PRLiftsCore

struct SettingsScreen: View {
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false
    @Environment(\.modelContext) private var modelContext
    @State private var viewModel = AccountDeletionViewModel()

    var body: some View {
        NavigationStack {
            ZStack {
                Color.prBackground.ignoresSafeArea()
                accountSection
                    .padding(.horizontal, PRSpacing.screenHorizontal)
                    .padding(.top, PRSpacing.medium)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)

                if viewModel.isDeleting {
                    Color.black.opacity(0.45)
                        .ignoresSafeArea()
                    ProgressView()
                        .scaleEffect(1.5)
                        .tint(.white)
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.large)
        }
        .confirmationDialog(
            "Delete Account",
            isPresented: $viewModel.isShowingConfirmation,
            titleVisibility: .visible
        ) {
            Button("Delete My Account", role: .destructive) {
                Task {
                    let success = await viewModel.performDeletion(
                        cancelSync: {},
                        clearLocalData: { try modelContext.delete(model: User.self) },
                        clearKeychain: {}
                    )
                    if success { hasCompletedOnboarding = false }
                }
            }
            Button("Cancel", role: .cancel) {
                viewModel.cancelDeletion()
            }
            .accessibilityIdentifier("CancelDeleteAccount")
        } message: {
            Text(
                "This permanently deletes your account and all your data. This cannot be undone."
            )
        }
        .alert(
            "Couldn't Delete Account",
            isPresented: Binding(
                get: { viewModel.errorMessage != nil },
                set: { if !$0 { viewModel.dismissError() } }
            )
        ) {
            Button("OK") { viewModel.dismissError() }
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
        .disabled(viewModel.isDeleting)
        .accessibilityLabel(viewModel.isDeleting ? "Deleting account, please wait" : "")
    }

    private var accountSection: some View {
        VStack(alignment: .leading, spacing: PRSpacing.small) {
            Text("Account")
                .font(.prCaption)
                .foregroundColor(.prTextSecondary)
                .textCase(.uppercase)
                .tracking(0.5)
                .accessibilityAddTraits(.isHeader)

            PRButton(
                label: "Delete Account",
                variant: .destructive,
                isLoading: viewModel.isDeleting,
                isDisabled: viewModel.isDeleting
            ) {
                viewModel.requestDeletion()
            }
            .accessibilityIdentifier("DeleteAccountButton")
        }
    }
}

#Preview {
    SettingsScreen()
        .preferredColorScheme(.dark)
}

#Preview("Light") {
    SettingsScreen()
        .preferredColorScheme(.light)
}
