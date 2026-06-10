import kotlin.system.exitProcess

/**
 * Tiny, framework-free test runner for [JsonParser]. It avoids kotlin-test so the
 * example needs only the Kotlin compiler from setup-kotlin (no extra classpath).
 * Any failed assertion prints to stderr and exits non-zero, which fails the CI
 * matrix leg; a clean run prints "All tests passed." and exits 0.
 */

private var failures = 0

private fun <T> assertEquals(expected: T, actual: T, msg: String) {
    if (expected != actual) {
        System.err.println("FAIL: $msg -> expected <$expected>, got <$actual>")
        failures++
    } else {
        println("PASS: $msg")
    }
}

fun main() {
    val sample = """
        {
          "os": ["ubuntu-latest", "macos-latest"],
          "versions": { "kotlin": ["2.4.0", "2.3.10"] },
          "ghpages_branch": "gh-pages"
        }
    """.trimIndent()

    assertEquals(
        listOf("ubuntu-latest", "macos-latest"),
        JsonParser.parseStringArray(sample, "os"),
        "parse the os array",
    )
    assertEquals(
        listOf("2.4.0", "2.3.10"),
        JsonParser.parseStringArray(sample, "kotlin"),
        "parse the kotlin versions",
    )
    assertEquals(
        emptyList(),
        JsonParser.parseStringArray(sample, "missing"),
        "absent key yields an empty list",
    )

    if (failures > 0) {
        System.err.println("$failures test(s) failed.")
        exitProcess(1)
    }
    println("All tests passed.")
}
