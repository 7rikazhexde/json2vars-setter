using System.Text.Json;
using JsonVarsSetter;
using Xunit;

namespace JsonVarsSetter.Tests;

public class JsonParserTests
{
    private readonly string _configPath =
        Path.Combine(AppContext.BaseDirectory, "dotnet_project_matrix.json");

    [Fact]
    public void ParsesJsonFile()
    {
        var result = JsonParser.ParseConfig(_configPath);
        Assert.NotNull(result);
    }

    [Fact]
    public void ParsesExpectedValues()
    {
        var result = JsonParser.ParseConfig(_configPath);
        Assert.NotNull(result);

        var os = result!["os"].EnumerateArray()
            .Select(e => e.GetString())
            .ToList();
        Assert.Contains("ubuntu-latest", os);
        Assert.Contains("windows-latest", os);
        Assert.Contains("macos-latest", os);

        var versions = result["versions"].GetProperty("dotnet").EnumerateArray()
            .Select(e => e.GetString())
            .ToList();
        Assert.Equal(new[] { "8.0", "9.0" }, versions);

        Assert.Equal("ghgapes", result["ghpages_branch"].GetString());
    }

    [Fact]
    public void ReturnsNullForMissingFile()
    {
        var result = JsonParser.ParseConfig("non-existent.json", silent: true);
        Assert.Null(result);
    }
}
