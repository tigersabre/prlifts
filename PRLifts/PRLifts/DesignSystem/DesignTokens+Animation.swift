import SwiftUI

enum PRAnimation {
    static let standard    = Animation.easeInOut(duration: 0.25)
    static let quick       = Animation.easeOut(duration: 0.15)
    static let celebration = Animation.spring(response: 0.4, dampingFraction: 0.6)
    static let sheet       = Animation.spring(response: 0.35, dampingFraction: 0.85)
}
