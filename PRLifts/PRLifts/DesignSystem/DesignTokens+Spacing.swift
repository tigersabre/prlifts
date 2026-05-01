import SwiftUI

enum PRSpacing {
    static let xxxSmall: CGFloat = 4
    static let xxSmall:  CGFloat = 8
    static let xSmall:   CGFloat = 12
    static let small:    CGFloat = 16
    static let medium:   CGFloat = 20
    static let large:    CGFloat = 24
    static let xLarge:   CGFloat = 32
    static let xxLarge:  CGFloat = 48
    static let xxxLarge: CGFloat = 64

    static let screenHorizontal:  CGFloat = small
    static let cardPadding:       CGFloat = small
    static let cardGap:           CGFloat = xxSmall
    static let buttonHeight:      CGFloat = 50
    static let minimumTouchTarget: CGFloat = 44
}

struct PRShadow {
    let color: Color
    let radius: CGFloat
    let x: CGFloat
    let y: CGFloat

    static let low    = PRShadow(color: .black.opacity(0.12), radius: 4,  x: 0, y: 2)
    static let medium = PRShadow(color: .black.opacity(0.20), radius: 8,  x: 0, y: 4)
    static let high   = PRShadow(color: .black.opacity(0.28), radius: 16, x: 0, y: 8)
    static let brand  = PRShadow(color: Color("PRBrand").opacity(0.35),  radius: 16, x: 0, y: 6)
    static let accent = PRShadow(color: Color("PRAccent").opacity(0.30), radius: 16, x: 0, y: 6)
}

enum PRRadius {
    static let small:  CGFloat = 6
    static let medium: CGFloat = 10
    static let large:  CGFloat = 16
    static let xLarge: CGFloat = 20
    static let pill:   CGFloat = 999
}
