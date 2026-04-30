import SwiftUI

extension Font {
    static let prDisplayLarge    = Font.system(size: 48, weight: .black,    design: .rounded)
    static let prDisplayMedium   = Font.system(size: 34, weight: .heavy,    design: .rounded)
    static let prHeadlineLarge   = Font.system(size: 22, weight: .bold,     design: .rounded)
    static let prHeadlineMedium  = Font.system(.headline)
    static let prBody            = Font.system(.body)
    static let prBodySecondary   = Font.system(.subheadline)
    static let prDataLarge       = Font.system(size: 28, weight: .semibold, design: .monospaced)
    static let prDataMedium      = Font.system(size: 20, weight: .medium,   design: .monospaced)
    static let prDataSmall       = Font.system(size: 15, weight: .medium,   design: .monospaced)
    static let prCaption         = Font.system(.caption)
    static let prCaptionSmall    = Font.system(.caption2)
    static let prButtonPrimary   = Font.system(.body).weight(.bold)
    static let prButtonSecondary = Font.system(.subheadline).weight(.medium)
}
