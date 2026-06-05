# PHP Example for json2vars-setter

This is a PHP implementation example for parsing JSON configuration files in GitHub Actions matrix testing.

## Requirements

- PHP >= 8.2
- Composer

## Project Structure

```bash
.
├── composer.json             # PHP dependencies and scripts
├── phpunit.xml               # PHPUnit configuration
├── php_project_matrix.json   # Matrix definition consumed by json2vars-setter
├── src/
│   └── JsonParser.php        # Main implementation
└── tests/
    └── JsonParserTest.php    # Test implementation
```

## Setup

Install dependencies with Composer:

```bash
cd examples/php
composer install
```

## Running

Run the parser directly:

```bash
composer start
# or
php src/JsonParser.php
```

Run the tests:

```bash
composer test
# or
vendor/bin/phpunit
```

## Matrix file

`php_project_matrix.json` defines the OS list and PHP versions used by the matrix
testing workflow. The PHP versions use the `major.minor` form accepted by
[`shivammathur/setup-php`](https://github.com/marketplace/actions/setup-php-action):

```json
{
    "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    "versions": {
        "php": ["8.2", "8.3", "8.4"]
    },
    "ghpages_branch": "ghgapes"
}
```

The `.github/workflows/php_test.yml` workflow reads this file through
json2vars-setter and runs the tests across every OS / PHP version combination.
