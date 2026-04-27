# PRLifts — Design Tokens and Component Standards

**Version:** 1.0
**Last updated:** April 2026
**Owner:** Design Systems Lead
**Audience:** iOS developers (human and Claude Code)

> Design tokens are the named constants for all visual values in the app.
> Never hardcode a color, font size, spacing value, or radius in SwiftUI.
> Always reference a token. This ensures visual consistency and makes
> future design changes a one-line edit.

---

## Why Tokens Matter

If colors are hardcoded, changing the brand color requires finding and
replacing every `Color(red: 0.2, green: 0.4, blue: 0.8)` in the codebase.
With tokens, it is a one-line change in `DesignTokens.swift`.

---

## Color Tokens

```swift
// DesignTokens+Colors.swift
// PRLifts iOS App
//
// All color values for PRLifts. Always use these constants.
// Never use raw Color(red:green:blue:) or hex strings in SwiftUI views.

extension Color {

    // ── Brand ────────────────────────────────────────────────────────────

    /// Primary brand color. Used for primary buttons, active states, links.
    static let prBrand = Color("PRBrand")            // Deep athletic blue

    /// Secondary brand color. Used for accents, highlights, PR achievements.
    static let prAccent = Color("PRAccent")           // Energetic gold/amber

    // ── Backgrounds ──────────────────────────────────────────────────────

    /// Primary background. Main screen background.
    static let prBackground = Color("PRBackground")   // System background (auto dark/light)

    /// Secondary background. Cards, sheets, grouped content.
    static let prBackgroundSecondary = Color("PRBackgroundSecondary")

    /// Tertiary background. Nested content, input fields.
    static let prBackgroundTertiary = Color("PRBackgroundTertiary")

    // ── Text ─────────────────────────────────────────────────────────────

    /// Primary text. Body copy, headlines.
    static let prTextPrimary = Color("PRTextPrimary")

    /// Secondary text. Subtitles, metadata, less important info.
    static let prTextSecondary = Color("PRTextSecondary")

    /// Tertiary text. Placeholders, disabled state labels.
    static let prTextTertiary = Color("PRTextTertiary")

    /// Text on brand-colored surfaces (buttons, banners).
    static let prTextOnBrand = Color("PRTextOnBrand")

    // ── Semantic ─────────────────────────────────────────────────────────

    /// Success state. PR achieved, sync complete, positive feedback.
    static let prSuccess = Color("PRSuccess")         // Green

    /// Warning state. Rate limit approaching, optional items.
    static let prWarning = Color("PRWarning")         // Amber

    /// Error state. Failed operations, validation errors.
    static let prError = Color("PRError")             // Red

    /// Offline state. Sync pending, connectivity lost.
    static let prOffline = Color("PROffline")         // Muted blue-grey

    // ── PR Celebration ───────────────────────────────────────────────────

    /// Used exclusively for PR achievement celebrations.
    /// Not for general accent use.
    static let prCelebration = Color("PRCelebration") // Gold gradient start
    static let prCelebrationEnd = Color("PRCelebrationEnd") // Gold gradient end
}
```

**Asset catalog configuration:**
All colors are defined in `Assets.xcassets/Colors/` with light and dark
mode variants. This gives automatic dark mode support without any code.

---

## Typography Tokens

```swift
// DesignTokens+Typography.swift
// PRLifts iOS App
//
// All text styles for PRLifts. Always use Font extensions — never
// hardcode font sizes or weights. All fonts support Dynamic Type.

extension Font {

    // ── Display ──────────────────────────────────────────────────────────

    /// Hero numbers: PR values, large stats. 48pt.
    static let prDisplayLarge = Font.system(size: 48, weight: .bold, design: .rounded)

    /// Section headlines, screen titles. 34pt.
    static let prDisplayMedium = Font.system(size: 34, weight: .bold, design: .rounded)

    // ── Headline ─────────────────────────────────────────────────────────

    /// Card titles, exercise names. 22pt.
    static let prHeadlineLarge = Font.system(.title2, design: .rounded).weight(.semibold)

    /// Sub-section titles, set headers. 17pt.
    static let prHeadlineMedium = Font.system(.headline, design: .default)

    // ── Body ─────────────────────────────────────────────────────────────

    /// Primary body copy. 17pt. Most UI text.
    static let prBody = Font.system(.body, design: .default)

    /// Secondary body copy. 15pt. Metadata, descriptions.
    static let prBodySecondary = Font.system(.subheadline, design: .default)

    // ── Data ─────────────────────────────────────────────────────────────

    /// Numeric data: weights, reps, distances. Monospace for alignment.
    static let prDataLarge = Font.system(size: 28, weight: .semibold, design: .monospaced)
    static let prDataMedium = Font.system(size: 20, weight: .medium, design: .monospaced)
    static let prDataSmall = Font.system(size: 15, weight: .medium, design: .monospaced)

    // ── Caption ──────────────────────────────────────────────────────────

    /// Labels, tags, badges. 13pt.
    static let prCaption = Font.system(.caption, design: .default)

    /// Smallest labels. 11pt. Use sparingly.
    static let prCaptionSmall = Font.system(.caption2, design: .default)

    // ── Button ───────────────────────────────────────────────────────────

    /// Primary button label. 17pt semibold.
    static let prButtonPrimary = Font.system(.body, design: .default).weight(.semibold)

    /// Secondary button label. 15pt medium.
    static let prButtonSecondary = Font.system(.subheadline, design: .default).weight(.medium)
}
```

**Dynamic Type:** All fonts use Apple's semantic sizes (`.body`, `.headline`, etc.)
or explicit sizes that scale with the user's text size setting. Never override
`dynamicTypeSize` to disable scaling.

---

## Spacing Tokens

```swift
// DesignTokens+Spacing.swift
// PRLifts iOS App
//
// All spacing values. Use these constants for padding, margins,
// and gaps. Never use magic numbers like .padding(13).

enum PRSpacing {

    /// 4pt. Minimum spacing. Icon-to-label, tight groupings.
    static let xxxSmall: CGFloat = 4

    /// 8pt. Small spacing. Within components, related elements.
    static let xxSmall: CGFloat = 8

    /// 12pt. Medium-small. Section padding, card internals.
    static let xSmall: CGFloat = 12

    /// 16pt. Standard spacing. Most padding, between related groups.
    static let small: CGFloat = 16

    /// 20pt. Medium spacing. Between cards, list items.
    static let medium: CGFloat = 20

    /// 24pt. Medium-large. Section separation.
    static let large: CGFloat = 24

    /// 32pt. Large spacing. Screen-level breathing room.
    static let xLarge: CGFloat = 32

    /// 48pt. Extra-large. Onboarding spacing, hero sections.
    static let xxLarge: CGFloat = 48

    /// 64pt. Maximum spacing. Large screen whitespace.
    static let xxxLarge: CGFloat = 64

    // ── Semantic Aliases ─────────────────────────────────────────────────

    /// Standard screen horizontal padding.
    static let screenHorizontal: CGFloat = small       // 16pt

    /// Standard screen top padding below navigation.
    static let screenTop: CGFloat = medium             // 20pt

    /// Padding inside cards and list cells.
    static let cardPadding: CGFloat = small            // 16pt

    /// Gap between cards in a list.
    static let cardGap: CGFloat = xxSmall              // 8pt

    /// Standard button height (also minimum touch target).
    static let buttonHeight: CGFloat = 50

    /// Minimum touch target for any interactive element.
    static let minimumTouchTarget: CGFloat = 44
}
```

---

## Corner Radius Tokens

```swift
enum PRRadius {
    /// Subtle rounding. Chips, badges, tags.
    static let small: CGFloat = 6

    /// Standard rounding. Input fields, small cards.
    static let medium: CGFloat = 10

    /// Prominent rounding. Cards, sheets, major UI elements.
    static let large: CGFloat = 16

    /// Capsule rounding. Primary buttons, pill shapes.
    static let pill: CGFloat = 999    // Renders as full capsule
}
```

---

## Shadow Tokens

```swift
struct PRShadow {
    let color: Color
    let radius: CGFloat
    let x: CGFloat
    let y: CGFloat

    /// Subtle elevation. Floating buttons, cards on background.
    static let low = PRShadow(
        color: .black.opacity(0.08),
        radius: 4, x: 0, y: 2
    )

    /// Standard elevation. Cards, dropdowns.
    static let medium = PRShadow(
        color: .black.opacity(0.12),
        radius: 8, x: 0, y: 4
    )

    /// High elevation. Sheets, modals (rarely needed — prefer system sheets).
    static let high = PRShadow(
        color: .black.opacity(0.16),
        radius: 16, x: 0, y: 8
    )
}

// Usage:
// .shadow(color: PRShadow.medium.color, radius: PRShadow.medium.radius,
//         x: PRShadow.medium.x, y: PRShadow.medium.y)
```

---

## Reusable Component Standards

### PRButton

The standard button component used throughout the app.

```swift
// PRButton.swift
// PRLifts iOS App
//
// Standard button component. All interactive buttons in the app
// should use PRButton or be consistent with its visual spec.
// Never create ad-hoc button styling in views.

enum PRButtonStyle {
    case primary    // Filled brand color. Main CTA.
    case secondary  // Outlined. Supporting action.
    case destructive // Red filled. Delete, revoke consent.
    case ghost      // No background. Navigation, subtle actions.
}

struct PRButton: View {
    let title: String
    let style: PRButtonStyle
    let action: () -> Void
    var isLoading: Bool = false
    var isDisabled: Bool = false

    var body: some View {
        Button(action: action) {
            // Implementation follows design token spec
        }
        .frame(minWidth: PRSpacing.minimumTouchTarget,
               minHeight: PRSpacing.buttonHeight)
        .disabled(isDisabled || isLoading)
        .accessibilityLabel(title)
    }
}
```

### PRCard

The standard card container.

```swift
struct PRCard<Content: View>: View {
    let content: () -> Content

    var body: some View {
        content()
            .padding(PRSpacing.cardPadding)
            .background(Color.prBackgroundSecondary)
            .cornerRadius(PRRadius.large)
            .shadow(color: PRShadow.low.color,
                    radius: PRShadow.low.radius,
                    x: PRShadow.low.x,
                    y: PRShadow.low.y)
    }
}
```

### PREmptyState

Standard empty state component. All empty screens use this.

```swift
struct PREmptyState: View {
    let icon: String           // SF Symbol name
    let heading: String        // "No workouts yet"
    let actionLabel: String    // "Log your first workout"
    let action: () -> Void

    var body: some View {
        VStack(spacing: PRSpacing.medium) {
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundColor(.prTextTertiary)
                .accessibilityHidden(true)

            Text(heading)
                .font(.prHeadlineMedium)
                .foregroundColor(.prTextSecondary)

            PRButton(title: actionLabel, style: .primary, action: action)
        }
        .padding(PRSpacing.xxLarge)
        .accessibilityElement(children: .combine)
    }
}
```

### PRLoadingSkeleton

Skeleton screen for loading states.

```swift
// Usage: Show while data is loading to avoid layout shift
struct PRLoadingSkeleton: View {
    var body: some View {
        RoundedRectangle(cornerRadius: PRRadius.small)
            .fill(Color.prBackgroundTertiary)
            .shimmering()  // Custom shimmer modifier
    }
}
```

---

## Animation Standards

```swift
enum PRAnimation {
    /// Standard UI transitions. Most screen changes.
    static let standard = Animation.easeInOut(duration: 0.25)

    /// Quick micro-interactions. Button press, toggle.
    static let quick = Animation.easeOut(duration: 0.15)

    /// PR celebration animation. Slower for impact.
    static let celebration = Animation.spring(response: 0.4, dampingFraction: 0.6)
}
```

---

## Dark Mode

All colors are defined with light and dark variants in the asset catalog.
No manual `colorScheme` environment checks are needed for standard colors.

If a view needs to respond to dark mode (e.g., an image that changes),
use the environment value:

```swift
@Environment(\.colorScheme) var colorScheme
```

Never hardcode light-mode-only colors in dark mode contexts.

