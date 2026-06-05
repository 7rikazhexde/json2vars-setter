import { assertEquals } from "jsr:@std/assert@^1.0.0";
import { parseConfig } from "./json_parser.ts";

const configUrl = new URL("./deno_project_matrix.json", import.meta.url);

Deno.test("parses the JSON file", () => {
  const result = parseConfig(configUrl);
  assertEquals(typeof result, "object");
  assertEquals(result !== null, true);
});

Deno.test("parses the expected values", () => {
  const result = parseConfig(configUrl) as Record<string, unknown>;

  const os = result["os"] as string[];
  assertEquals(os.includes("ubuntu-latest"), true);
  assertEquals(os.includes("windows-latest"), true);
  assertEquals(os.includes("macos-latest"), true);

  const versions = result["versions"] as Record<string, string[]>;
  assertEquals(versions["deno"], ["v1.x", "v2.x"]);

  assertEquals(result["ghpages_branch"], "ghgapes");
});

Deno.test("returns null for a missing file", () => {
  const result = parseConfig("non-existent.json", true);
  assertEquals(result, null);
});
