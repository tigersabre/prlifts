import Foundation
import SwiftData

@Model
public final class SupportReport {
    public var id: UUID
    public var deviceModel: String
    public var iosVersion: String
    public var appVersion: String
    // Mapped from pg column 'description' — renamed because @Model synthesises
    // CustomStringConvertible and reserves that property name.
    public var reportDescription: String
    public var syncLogUploaded: Bool

    public var user: User?

    public init(
        id: UUID = UUID(),
        deviceModel: String,
        iosVersion: String,
        appVersion: String,
        reportDescription: String,
        syncLogUploaded: Bool = false
    ) {
        self.id = id
        self.deviceModel = deviceModel
        self.iosVersion = iosVersion
        self.appVersion = appVersion
        self.reportDescription = reportDescription
        self.syncLogUploaded = syncLogUploaded
    }
}
