// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "Calorigram",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "Calorigram",
            targets: ["Calorigram"]),
    ],
    dependencies: [
        // Alamofire для HTTP запросов (опционально, можно использовать URLSession)
        // .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.8.0"),
        // KeychainAccess для работы с Keychain
        // .package(url: "https://github.com/kishikawakatsumi/KeychainAccess.git", from: "4.2.0"),
    ],
    targets: [
        .target(
            name: "Calorigram",
            dependencies: []),
        .testTarget(
            name: "CalorigramTests",
            dependencies: ["Calorigram"]),
    ]
)
