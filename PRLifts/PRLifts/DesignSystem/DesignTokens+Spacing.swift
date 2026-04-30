import CoreFoundation

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

enum PRRadius {
    static let small:  CGFloat = 6
    static let medium: CGFloat = 10
    static let large:  CGFloat = 16
    static let xLarge: CGFloat = 20
    static let pill:   CGFloat = 999
}
