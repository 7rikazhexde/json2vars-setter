<?php

declare(strict_types=1);

namespace JsonVarsSetter;

/**
 * Minimal JSON configuration parser used to demonstrate consuming the
 * json2vars-setter matrix file in a PHP project.
 */
final class JsonParser
{
    /**
     * Parse a JSON configuration file into an associative array.
     *
     * @param string $filePath Path to the JSON file.
     * @param bool   $silent   When true, suppress error output.
     *
     * @return array<string, mixed>|null The parsed data, or null on failure.
     */
    public static function parseConfig(string $filePath, bool $silent = false): ?array
    {
        try {
            $contents = @file_get_contents($filePath);
            if ($contents === false) {
                throw new \RuntimeException("Unable to read file: {$filePath}");
            }

            /** @var array<string, mixed> $data */
            $data = json_decode($contents, true, 512, JSON_THROW_ON_ERROR);

            return $data;
        } catch (\Throwable $e) {
            if (!$silent) {
                fwrite(STDERR, "Error reading or parsing JSON: {$e->getMessage()}\n");
            }

            return null;
        }
    }
}

// Allow running the file directly: `php src/JsonParser.php`
if (PHP_SAPI === 'cli' && isset($argv[0]) && realpath($argv[0]) === __FILE__) {
    $configPath = __DIR__ . '/../php_project_matrix.json';
    $result = JsonParser::parseConfig($configPath);
    if ($result !== null) {
        echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
    }
}
