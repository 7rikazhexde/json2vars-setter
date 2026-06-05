package io.github.json2varssetter;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.io.IOException;

/**
 * Minimal JSON configuration parser used to demonstrate consuming the
 * json2vars-setter matrix file in a Java project.
 */
public final class JsonParser {

    private JsonParser() {
    }

    /**
     * Parse a JSON configuration file into a JsonNode tree.
     *
     * @param filePath path to the JSON file
     * @return the parsed tree, or {@code null} on failure
     */
    public static JsonNode parseConfig(String filePath) {
        return parseConfig(filePath, false);
    }

    /**
     * Parse a JSON configuration file into a JsonNode tree.
     *
     * @param filePath path to the JSON file
     * @param silent   when true, suppress error output
     * @return the parsed tree, or {@code null} on failure
     */
    public static JsonNode parseConfig(String filePath, boolean silent) {
        try {
            return new ObjectMapper().readTree(new File(filePath));
        } catch (IOException e) {
            if (!silent) {
                System.err.println("Error reading or parsing JSON: " + e.getMessage());
            }
            return null;
        }
    }
}
