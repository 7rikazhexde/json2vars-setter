# Test runner for json_parser.jl using Julia's built-in `Test` standard
# library. A failing `@testset` exits non-zero, which fails the CI matrix leg.

using Test

include("json_parser.jl")

const SAMPLE = """
{
  "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
  "versions": { "julia": ["1.10", "1.11"] },
  "ghpages_branch": "ghgapes"
}
"""

@testset "json_parser" begin
    config = parse_config(SAMPLE)
    @test config !== nothing

    os = config["os"]
    @test length(os) == 3
    @test "ubuntu-latest" in os
    @test "windows-latest" in os
    @test "macos-latest" in os

    # Assert structure, not specific version values, so bumping the matrix
    # versions never requires editing this test.
    versions = config["versions"]["julia"]
    @test !isempty(versions)
    @test all(v -> !isempty(v), versions)

    @test config["ghpages_branch"] == "ghgapes"

    @test parse_config("not json"; silent = true) === nothing
end
