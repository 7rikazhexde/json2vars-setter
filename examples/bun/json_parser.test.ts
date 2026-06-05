import { describe, expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { parseConfig } from "./json_parser.ts";

const configPath = fileURLToPath(
  new URL("./bun_project_matrix.json", import.meta.url),
);

describe("parseConfig", () => {
  test("parses the JSON file", () => {
    const result = parseConfig(configPath);
    expect(result).not.toBeNull();
  });

  test("parses the expected values", () => {
    const result = parseConfig(configPath) as Record<string, unknown>;

    const os = result["os"] as string[];
    expect(os).toContain("ubuntu-latest");
    expect(os).toContain("windows-latest");
    expect(os).toContain("macos-latest");

    const versions = result["versions"] as Record<string, string[]>;
    expect(versions["bun"]).toEqual(["1.2.x", "1.3.x"]);

    expect(result["ghpages_branch"]).toBe("ghgapes");
  });

  test("returns null for a missing file", () => {
    const result = parseConfig("non-existent.json", true);
    expect(result).toBeNull();
  });
});
