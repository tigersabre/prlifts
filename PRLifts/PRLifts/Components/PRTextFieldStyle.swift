import SwiftUI

struct PRInputFieldStyle: ViewModifier {
    let isFocused: Bool
    var height: CGFloat = 52

    func body(content: Content) -> some View {
        content
            .padding(.horizontal, PRSpacing.small)
            .frame(height: height)
            .background(Color.prBackgroundTer)
            .clipShape(RoundedRectangle(cornerRadius: PRRadius.medium))
            .overlay(
                RoundedRectangle(cornerRadius: PRRadius.medium)
                    .stroke(borderColor, lineWidth: borderWidth)
            )
            .shadow(color: shadowColor, radius: 8, x: 0, y: 0)
    }

    private var borderColor: Color {
        isFocused ? Color.prBrandLight : Color.prBorder
    }

    private var borderWidth: CGFloat {
        isFocused ? 2 : 1
    }

    private var shadowColor: Color {
        isFocused ? Color.prBrand.opacity(0.15) : .clear
    }
}

extension View {
    func prInputFieldStyle(isFocused: Bool, height: CGFloat = 52) -> some View {
        modifier(PRInputFieldStyle(isFocused: isFocused, height: height))
    }
}
