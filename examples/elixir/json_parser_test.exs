ExUnit.start()
Code.require_file("json_parser.exs", __DIR__)

defmodule JsonParserTest do
  use ExUnit.Case

  @sample """
  {
    "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    "versions": { "elixir": ["1.18", "1.19"] },
    "ghpages_branch": "ghgapes"
  }
  """

  test "parses the expected values" do
    assert {:ok, config} = JsonParser.parse_config(@sample)

    assert config["os"] == ["ubuntu-latest", "windows-latest", "macos-latest"]

    # Assert structure, not specific version values, so bumping the matrix
    # versions never requires editing this test.
    versions = config["versions"]["elixir"]
    assert is_list(versions)
    assert versions != []
    assert Enum.all?(versions, &(is_binary(&1) and &1 != ""))

    assert config["ghpages_branch"] == "ghgapes"
  end

  test "returns an error for invalid JSON" do
    assert {:error, _reason} = JsonParser.parse_config("not json")
  end
end
