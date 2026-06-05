// Minimal JSON configuration parser used to demonstrate consuming the
// json2vars-setter matrix file in a Deno project.

export function parseConfig(
  filePath: string | URL,
  silent = false,
): Record<string, unknown> | null {
  try {
    const contents = Deno.readTextFileSync(filePath);
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
  const result = parseConfig(
    new URL("./deno_project_matrix.json", import.meta.url),
  );
  if (result !== null) {
    console.log(JSON.stringify(result, null, 2));
  }
}
