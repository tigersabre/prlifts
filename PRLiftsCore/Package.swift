// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "PRLiftsCore",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .library(name: "PRLiftsCore", targets: ["PRLiftsCore"]),
        .library(name: "PRLiftsCoreTestSupport", targets: ["PRLiftsCoreTestSupport"])
    ],
    targets: [
        .target(name: "PRLiftsCore"),
        .target(
            name: "PRLiftsCoreTestSupport",
            dependencies: ["PRLiftsCore"]
        ),
        .testTarget(
            name: "PRLiftsCoreTests",
            dependencies: ["PRLiftsCore", "PRLiftsCoreTestSupport"]
        )
    ]
)
