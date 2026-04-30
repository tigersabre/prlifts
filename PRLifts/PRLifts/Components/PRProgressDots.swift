import SwiftUI

struct PRProgressDots: View {
    let total: Int
    let current: Int

    var body: some View {
        HStack(spacing: 6) {
            ForEach(1...total, id: \.self) { step in
                RoundedRectangle(cornerRadius: 999)
                    .fill(step == current ? Color.prBrand : Color.prBackgroundTer)
                    .frame(width: step == current ? 20 : 6, height: 6)
                    .animation(PRAnimation.standard, value: current)
            }
        }
        .accessibilityLabel("Step \(current) of \(total)")
    }
}
