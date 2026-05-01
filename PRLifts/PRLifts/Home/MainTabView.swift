import SwiftUI

enum PRTab { case home, history, exercises, profile }

struct MainTabView: View {
    @State private var selectedTab: PRTab = .home

    init() {
        UITabBar.appearance().backgroundColor = UIColor(Color.prBackgroundSec)
        UITabBar.appearance().unselectedItemTintColor = UIColor(Color.prTextTertiary)
    }

    var body: some View {
        TabView(selection: $selectedTab) {
            HomeScreen()
                .tabItem { Label("Home", systemImage: "house.fill") }
                .tag(PRTab.home)
            HistoryPlaceholderView()
                .tabItem { Label("History", systemImage: "clock.arrow.circlepath") }
                .tag(PRTab.history)
            ExercisesPlaceholderView()
                .tabItem { Label("Exercises", systemImage: "list.bullet") }
                .tag(PRTab.exercises)
            ProfilePlaceholderView()
                .tabItem { Label("Profile", systemImage: "person.circle") }
                .tag(PRTab.profile)
        }
        .tint(Color.prBrand)
    }
}

#Preview {
    MainTabView()
}
