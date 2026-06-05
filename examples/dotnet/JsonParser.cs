using System.Text.Json;

namespace JsonVarsSetter;

/// <summary>
/// Minimal JSON configuration parser used to demonstrate consuming the
/// json2vars-setter matrix file in a .NET (C#) project.
/// </summary>
public static class JsonParser
{
    /// <summary>
    /// Parse a JSON configuration file into a dictionary of JSON elements.
    /// </summary>
    /// <param name="filePath">Path to the JSON file.</param>
    /// <param name="silent">When true, suppress error output.</param>
    /// <returns>The parsed data, or null on failure.</returns>
    public static Dictionary<string, JsonElement>? ParseConfig(
        string filePath,
        bool silent = false)
    {
        try
        {
            var contents = File.ReadAllText(filePath);
            return JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(contents);
        }
        catch (Exception e)
        {
            if (!silent)
            {
                Console.Error.WriteLine($"Error reading or parsing JSON: {e.Message}");
            }

            return null;
        }
    }
}
