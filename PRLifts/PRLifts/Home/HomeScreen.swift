import SwiftUI

struct HomeScreen: View {
    var body: some View {
        Text("PRLifts")
            .font(.prDisplayMedium)
            .foregroundColor(.prTextPrimary)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color.prBackground.ignoresSafeArea())
    }
}

#Preview {
    HomeScreen()
}
