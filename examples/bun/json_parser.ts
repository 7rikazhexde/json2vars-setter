// Minimal JSON configuration parser used to demonstrate consuming the
// json2vars-setter matrix file in a Bun project.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export function parseConfig(
  filePath: string,
  silent = false,
): Record<string, unknown> | null {
  try {
    const contents = readFileSync(filePath, "utf-8");
    return JSON.parse(contents) as Record<string, unknown>;
  } catch (e) {
    if (!silent) {
      const message = e instanceof Error ? e.message : String(e);
      console.error(`Error reading or parsing JSON: ${message}`);
    }
    return null;
  }
}

if (import.meta.main) {
  const configPath = fileURLToPath(
    new URL("./bun_project_matrix.json", import.meta.url),
  );
  const result = parseConfig(configPath);
  if (result !== null) {
    console.log(JSON.stringify(result, null, 2));
  }
}
