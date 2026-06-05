# .NET (C#) Example for json2vars-setter

This is a .NET (C#) implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- .NET SDK 8.0 or newer

## Project Structure

```bash
.
├── JsonParserExample.csproj   # Project + test dependencies (xUnit)
├── JsonParser.cs              # Main implementation
├── JsonParserTests.cs         # Test implementation
└── dotnet_project_matrix.json # Matrix definition consumed by json2vars-setter
```

## Setup & Running

Restore and run the tests:

```bash
cd examples/dotnet
dotnet test
```

## Matrix file

`dotnet_project_matrix.json` defines the OS list and .NET versions used by the matrix
testing workflow. The versions use the channel form accepted by
[`actions/setup-dotnet`](https://github.com/marketplace/actions/setup-dotnet):

```json
{
    "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    "versions": {
        "dotnet": ["8.0", "9.0"]
    },
    "ghpages_branch": "ghgapes"
}
```

The project targets `net8.0` with `RollForward=LatestMajor`, so the same test
assembly builds and runs on every SDK in the matrix. The
`.github/workflows/dotnet_test.yml` workflow reads this file through json2vars-setter
and runs the tests across every OS / .NET version combination.
