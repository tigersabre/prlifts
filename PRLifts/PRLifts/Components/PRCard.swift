import SwiftUI

struct PRCard<Content: View>: View {
    var padding: CGFloat = PRSpacing.cardPadding
    var radius: CGFloat = PRRadius.large
    @ViewBuilder let content: () -> Content

    var body: some View {
        content()
            .padding(padding)
            .background(Color.prBackgroundSec)
            .clipShape(RoundedRectangle(cornerRadius: radius))
            .overlay(
                RoundedRectangle(cornerRadius: radius)
                    .stroke(Color.prBorder, lineWidth: 1)
            )
            .shadow(
                color: PRShadow.low.color,
                radius: PRShadow.low.radius,
                x: PRShadow.low.x,
                y: PRShadow.low.y
            )
    }
}
