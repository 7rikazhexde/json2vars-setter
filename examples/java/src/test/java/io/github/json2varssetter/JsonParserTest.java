package io.github.json2varssetter;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.nio.file.Paths;
import org.junit.jupiter.api.Test;

class JsonParserTest {

    private final String configPath =
        Paths.get("java_project_matrix.json").toString();

    @Test
    void parsesJsonFile() {
        JsonNode result = JsonParser.parseConfig(configPath);
        assertNotNull(result);
    }

    @Test
    void parsesExpectedValues() {
        JsonNode result = JsonParser.parseConfig(configPath);
        assertNotNull(result);

        JsonNode os = result.get("os");
        assertTrue(os.toString().contains("ubuntu-latest"));
        assertTrue(os.toString().contains("windows-latest"));
        assertTrue(os.toString().contains("macos-latest"));

        JsonNode versions = result.get("versions").get("java");
        assertEquals("[\"11\",\"17\",\"21\"]", versions.toString());

        assertEquals("ghgapes", result.get("ghpages_branch").asText());
    }

    @Test
    void returnsNullForMissingFile() {
        JsonNode result = JsonParser.parseConfig("non-existent.json", true);
        assertNull(result);
    }
}
