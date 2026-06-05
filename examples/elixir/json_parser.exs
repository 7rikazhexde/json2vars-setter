defmodule JsonParser do
  @moduledoc """
  Minimal JSON configuration parser used to demonstrate consuming the
  json2vars-setter matrix file in an Elixir project. It relies on the built-in
  `JSON` module (standard library since Elixir 1.18), so no external
  dependencies are required.
  """

  @doc """
  Parse `data` (a JSON string) into a map.

  Returns `{:ok, map}` on success or `{:error, reason}` on failure.
  """
  def parse_config(data) when is_binary(data) do
    JSON.decode(data)
  end

  @doc """
  Read and print the example matrix file.
  """
  def main do
    path = Path.join(__DIR__, "elixir_project_matrix.json")

    case path |> File.read!() |> parse_config() do
      {:ok, config} -> IO.inspect(config, label: "matrix")
      {:error, reason} -> IO.puts("Error parsing JSON: #{inspect(reason)}")
    end
  end
end
