// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "json2vars_swift_example",
    targets: [
        .target(
            name: "JsonParserLib",
            path: "Sources/JsonParserLib"
        ),
        .testTarget(
            name: "JsonParserLibTests",
            dependencies: ["JsonParserLib"],
            path: "Tests/JsonParserLibTests"
        ),
    ]
)
