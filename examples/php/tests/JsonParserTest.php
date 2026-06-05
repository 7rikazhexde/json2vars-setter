<?php

declare(strict_types=1);

namespace JsonVarsSetter\Tests;

use JsonVarsSetter\JsonParser;
use PHPUnit\Framework\TestCase;

final class JsonParserTest extends TestCase
{
    private string $configPath;

    protected function setUp(): void
    {
        $this->configPath = __DIR__ . '/../php_project_matrix.json';
    }

    public function testParsesJsonFile(): void
    {
        $result = JsonParser::parseConfig($this->configPath);
        $this->assertIsArray($result);
    }

    public function testParsesExpectedValues(): void
    {
        $result = JsonParser::parseConfig($this->configPath);

        $this->assertIsArray($result);
        $this->assertContains('ubuntu-latest', $result['os']);
        $this->assertContains('windows-latest', $result['os']);
        $this->assertContains('macos-latest', $result['os']);
        $this->assertSame(['8.2', '8.3', '8.4'], $result['versions']['php']);
        $this->assertSame('ghgapes', $result['ghpages_branch']);
    }

    public function testReturnsNullForMissingFile(): void
    {
        $result = JsonParser::parseConfig('non-existent.json', true);
        $this->assertNull($result);
    }
}
