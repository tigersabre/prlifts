import SwiftUI

enum PRButtonVariant { case primary, secondary, destructive, ghost }

struct PRButton: View {
    let label: String
    var variant: PRButtonVariant = .primary
    var icon: String?
    var isLoading: Bool = false
    var isDisabled: Bool = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                if isLoading {
                    ProgressView().tint(labelColor).scaleEffect(0.85)
                }
                if let icon {
                    Image(systemName: icon)
                }
                Text(label).font(buttonFont)
            }
            .foregroundColor(labelColor)
            .frame(maxWidth: .infinity)
            .frame(height: PRSpacing.buttonHeight)
            .background(bgColor)
            .overlay(
                RoundedRectangle(cornerRadius: PRRadius.pill)
                    .stroke(Color.prBrand, lineWidth: variant == .secondary ? 1.5 : 0)
            )
            .clipShape(Capsule())
            .shadow(color: shadowColor, radius: shadowRadius, x: 0, y: 6)
        }
        .disabled(isDisabled || isLoading)
        .accessibilityLabel(label)
    }

    private var bgColor: Color {
        switch variant {
        case .primary:     return isDisabled ? .prBackgroundTer : .prBrand
        case .secondary:   return .clear
        case .destructive: return .prError
        case .ghost:       return .clear
        }
    }

    private var labelColor: Color {
        switch variant {
        case .primary:     return isDisabled ? .prTextTertiary : .prTextOnBrand
        case .secondary:   return .prBrandLight
        case .destructive: return .white
        case .ghost:       return .prTextSecondary
        }
    }

    private var buttonFont: Font {
        variant == .secondary ? .prButtonSecondary : .prButtonPrimary
    }

    private var shadowColor: Color {
        variant == .primary && !isDisabled ? Color.prBrand.opacity(0.35) : .clear
    }

    private var shadowRadius: CGFloat { variant == .primary ? 16 : 0 }
}
