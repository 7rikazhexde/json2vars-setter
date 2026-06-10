import java.io.File

/**
 * Minimal, dependency-free helper to consume the json2vars-setter matrix file in
 * a Kotlin project.
 *
 * It is intentionally tiny: it extracts the flat string arrays the matrix uses
 * (e.g. "os", or "kotlin" under "versions") with a small regex. That is enough to
 * demonstrate reading the action's output without pulling in a JSON library, so
 * the example compiles with nothing but the Kotlin compiler from setup-kotlin.
 */
object JsonParser {
    /**
     * Extract the first array of strings associated with [key] in [json].
     * Returns an empty list when the key is absent.
     */
    fun parseStringArray(json: String, key: String): List<String> {
        val arrayBody = Regex(
            "\"" + Regex.escape(key) + "\"\\s*:\\s*\\[(.*?)]",
            RegexOption.DOT_MATCHES_ALL,
        ).find(json)?.groupValues?.get(1) ?: return emptyList()

        return Regex("\"(.*?)\"").findAll(arrayBody).map { it.groupValues[1] }.toList()
    }

    /** Read a file as UTF-8 text. */
    fun readFile(path: String): String = File(path).readText()
}

fun main() {
    val json = JsonParser.readFile("kotlin_project_matrix.json")
    println("os: " + JsonParser.parseStringArray(json, "os"))
    println("kotlin: " + JsonParser.parseStringArray(json, "kotlin"))
}
