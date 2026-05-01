import SwiftUI
import PRLiftsCore

struct UnitPreferenceScreen: View {
    @Bindable var viewModel: OnboardingViewModel
    let onBack: () -> Void
    let onContinue: () -> Void

    var body: some View {
        ZStack {
            Color.prBackground.ignoresSafeArea()
            VStack(alignment: .leading, spacing: 0) {
                navBar
                PRProgressDots(total: 4, current: 4)
                    .padding(.top, PRSpacing.large)
                headline
                weightSection
                heightSection
                Spacer()
                PRButton(
                    label: "Start tracking",
                    isLoading: viewModel.isLoading
                ) {
                    Task {
                        if await viewModel.saveProfile() {
                            onContinue()
                        }
                    }
                }
                .padding(.bottom, PRSpacing.xLarge)
            }
            .padding(.horizontal, PRSpacing.screenHorizontal)
            stepLabel
            errorOverlay
        }
        .navigationBarHidden(true)
    }

    private var navBar: some View {
        HStack {
            Button(action: onBack) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(.prBrandLight)
                    .frame(width: PRSpacing.minimumTouchTarget, height: PRSpacing.minimumTouchTarget)
            }
            .accessibilityLabel("Back")
            Spacer()
        }
        .frame(height: 50)
    }

    private var headline: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("How do you measure?")
                .font(.prDisplayMedium)
                .foregroundColor(.prTextPrimary)
            Text("You can change this anytime in settings.")
                .font(.prBodySecondary)
                .foregroundColor(.prTextSecondary)
        }
        .padding(.top, PRSpacing.xSmall)
        .padding(.bottom, PRSpacing.xLarge)
    }

    private var weightSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("WEIGHT")
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.prTextTertiary)
                .tracking(0.6)

            HStack(spacing: 10) {
                UnitCard(
                    label: "lbs",
                    sublabel: "Pounds",
                    isSelected: viewModel.selectedWeightUnit == .lbs
                ) {
                    viewModel.selectedWeightUnit = .lbs
                }
                UnitCard(
                    label: "kg",
                    sublabel: "Kilograms",
                    isSelected: viewModel.selectedWeightUnit == .kg
                ) {
                    viewModel.selectedWeightUnit = .kg
                }
            }
        }
    }

    private var heightSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("HEIGHT")
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.prTextTertiary)
                .tracking(0.6)
                .padding(.top, PRSpacing.large)

            HStack(spacing: 10) {
                UnitCard(
                    label: "in",
                    sublabel: "Inches",
                    isSelected: viewModel.selectedMeasurementUnit == .inches
                ) {
                    viewModel.selectedMeasurementUnit = .inches
                }
                UnitCard(
                    label: "cm",
                    sublabel: "Centimeters",
                    isSelected: viewModel.selectedMeasurementUnit == .cm
                ) {
                    viewModel.selectedMeasurementUnit = .cm
                }
            }
        }
    }

    private var stepLabel: some View {
        VStack {
            Spacer()
            Text("Step 4 of 4 — almost there")
                .font(.system(size: 14))
                .foregroundColor(.prTextTertiary)
                .padding(.bottom, PRSpacing.small)
        }
    }

    @ViewBuilder
    private var errorOverlay: some View {
        if let message = viewModel.errorMessage {
            VStack {
                Spacer()
                Text(message)
                    .font(.prBodySecondary)
                    .foregroundColor(.prError)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, PRSpacing.screenHorizontal)
                    .padding(.bottom, 80)
            }
        }
    }
}

private struct UnitCard: View {
    let label: String
    let sublabel: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Text(label)
                    .font(.system(size: 28, weight: .heavy, design: .rounded))
                    .foregroundColor(isSelected ? .prBrand : .prTextSecondary)
                Text(sublabel)
                    .font(.system(size: 13))
                    .foregroundColor(isSelected ? .prBrandLight : .prTextTertiary)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 90)
            .background(isSelected ? Color.prBrand.opacity(0.18) : Color.prBackgroundSec)
            .clipShape(RoundedRectangle(cornerRadius: PRRadius.large))
            .overlay(
                RoundedRectangle(cornerRadius: PRRadius.large)
                    .stroke(isSelected ? Color.prBrand : Color.prBorder, lineWidth: isSelected ? 2 : 1)
            )
            .shadow(
                color: isSelected ? Color.prBrand.opacity(0.20) : .clear,
                radius: 8, x: 0, y: 0
            )
        }
        .contentShape(Rectangle())
        .animation(PRAnimation.quick, value: isSelected)
        .accessibilityLabel("\(label), \(sublabel)")
        .accessibilityIdentifier("\(label), \(sublabel)")
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }
}
