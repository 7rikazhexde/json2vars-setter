#!/usr/bin/env python3
"""
Dynamic update of matrix.json with latest or stable versions.
This script updates the matrix.json file with the requested version strategy without changing its structure.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, cast

from json2vars_setter.version.core.utils import JsonObject, VersionInfo
from json2vars_setter.version.registry import get_version_fetcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("matrix_update")


class VersionStrategy:
    """Defines which versions to include in matrix"""

    STABLE: str = "stable"
    LATEST: str = "latest"
    BOTH: str = "both"

    @classmethod
    def is_valid(cls, strategy: str) -> bool:
        """Check if the strategy is valid"""
        return strategy in [cls.STABLE, cls.LATEST, cls.BOTH]


def get_versions_from_strategy(version_info: VersionInfo, strategy: str) -> List[str]:
    """
    Get versions based on the specified strategy

    Args:
        version_info: Version information object
        strategy: Version selection strategy (stable, latest, or both)

    Returns:
        List of version strings selected according to the strategy

    Raises:
        ValueError: If strategy is invalid
    """
    if not VersionStrategy.is_valid(strategy):
        raise ValueError(f"Invalid strategy: {strategy}")

    versions: List[str] = []

    if strategy == VersionStrategy.STABLE or strategy == VersionStrategy.BOTH:
        if version_info.stable:
            versions.append(version_info.stable)

    if strategy == VersionStrategy.LATEST or strategy == VersionStrategy.BOTH:
        if version_info.latest and version_info.latest not in versions:
            versions.append(version_info.latest)

    return versions


def load_json_file(file_path: str) -> JsonObject:
    """
    Load a JSON file

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data as dictionary

    Raises:
        SystemExit: If file cannot be loaded
    """
    try:
        with open(file_path, "r") as f:
            data: JsonObject = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading JSON file: {e}")
        sys.exit(1)


def save_json_file(file_path: str, data: JsonObject) -> None:
    """
    Save a dictionary to a JSON file, ensuring it ends with a newline

    Args:
        file_path: Path where to save the JSON file
        data: Dictionary to save

    Raises:
        SystemExit: If file cannot be saved
    """
    try:
        # Convert to JSON with indentation
        json_content = json.dumps(data, indent=4)

        # Ensure the content ends with exactly one newline
        if not json_content.endswith("\n"):
            json_content += "\n"

        # Write to file
        with open(file_path, "w") as f:
            f.write(json_content)

        logger.info(f"Successfully saved to {file_path}")
    except (IOError, TypeError) as e:
        logger.error(f"Error saving JSON file: {e}")
        sys.exit(1)


def update_matrix_json(
    json_file: str, language_strategies: Dict[str, str], dry_run: bool = False
) -> None:
    """
    Update JSON file with latest versions based on specified strategies.

    Args:
        json_file: Path to the JSON file to update
        language_strategies: Dict mapping languages to version strategies
        dry_run: If True, don't write to file, just print what would be done

    Returns:
        None

    Raises:
        SystemExit: If file operations fail
        ValueError: If unsupported languages or strategies are specified
    """
    logger.info(f"Updating {json_file} with strategies: {language_strategies}")

    # Load existing JSON
    matrix_data = load_json_file(json_file)

    # Ensure versions key exists
    if "versions" not in matrix_data:
        matrix_data["versions"] = {}
    # The "versions" section maps each language to its list of versions.
    versions_section = cast(Dict[str, List[str]], matrix_data["versions"])

    # Backup original file
    if not dry_run:
        backup_file = f"{json_file}.bak"
        try:
            with open(json_file, "r") as src, open(backup_file, "w") as dst:
                dst.write(src.read())
            logger.info(f"Created backup at {backup_file}")
        except IOError as e:
            logger.warning(f"Could not create backup: {e}")

    # Keep track of changes
    changes: Dict[str, JsonObject] = {}

    # Update each language
    for language, strategy in language_strategies.items():
        try:
            logger.info(f"Processing {language} with strategy: {strategy}")

            # Fetch version info
            fetcher = get_version_fetcher(language)
            version_info = fetcher.fetch_versions()

            # Get versions based on strategy
            versions = get_versions_from_strategy(version_info, strategy)

            if not versions:
                logger.warning(f"No {strategy} versions found for {language}")
                continue

            # Create change log
            changes[language] = {
                "strategy": strategy,
                "versions": versions,
                "latest": version_info.latest or "",
                "stable": version_info.stable or "",
            }

            # Overwrite existing versions with new ones
            if language not in versions_section:
                versions_section[language] = []

            # Replace entirely with new versions (no appending)
            logger.info(f"Replacing {language} versions with: {versions}")
            versions_section[language] = versions

        except Exception as e:
            logger.error(f"Error updating {language} versions: {e}")
            logger.error("Full traceback:", exc_info=True)

    # Write updated JSON back to file
    if not dry_run:
        save_json_file(json_file, matrix_data)
        logger.info(f"Successfully updated {json_file}")
    else:
        logger.info("Dry run - would have written:")
        logger.info(json.dumps(matrix_data, indent=4))

    # Log changes
    logger.info("Changes summary:")
    for language, info in changes.items():
        logger.info(f"- {language} ({info['strategy']}):")
        logger.info(f"  - Latest: {info['latest']}")
        logger.info(f"  - Stable: {info['stable']}")
        logger.info(f"  - Set to: {', '.join(cast(List[str], info['versions']))}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the update-matrix command"""
    parser = argparse.ArgumentParser(
        description="""
Dynamically update matrix.json with latest or stable versions.

This script updates the matrix.json file with the requested version strategy
without changing its structure.

Examples:
  # Update all languages to latest versions with default JSON file
  python -m json2vars_setter.features.matrix_update --all latest

  # Update specific languages with custom JSON file
  python -m json2vars_setter.features.matrix_update --json-file custom_matrix.json --python stable --nodejs latest

  # Dry run with all languages and custom JSON file
  python -m json2vars_setter.features.matrix_update --json-file ./matrix.json --all both --dry-run

  # Verbose output with specific languages and default JSON file
  python -m json2vars_setter.features.matrix_update --ruby stable --go latest -v
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--json-file",
        default=os.path.join(".github", "json2vars-setter", "matrix.json"),
        help="Path to the JSON file to update (default: .github/json2vars-setter/matrix.json)",
    )
    parser.add_argument(
        "--python",
        choices=["stable", "latest", "both"],
        help="Strategy for Python versions",
    )
    parser.add_argument(
        "--nodejs",
        choices=["stable", "latest", "both"],
        help="Strategy for Node.js versions",
    )
    parser.add_argument(
        "--ruby",
        choices=["stable", "latest", "both"],
        help="Strategy for Ruby versions",
    )
    parser.add_argument(
        "--go", choices=["stable", "latest", "both"], help="Strategy for Go versions"
    )
    parser.add_argument(
        "--rust",
        choices=["stable", "latest", "both"],
        help="Strategy for Rust versions",
    )
    parser.add_argument(
        "--all",
        choices=["stable", "latest", "both"],
        help="Apply the same strategy to all languages",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write to file, just print what would be done",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    """Parse arguments and update the matrix JSON file"""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Apply --all to all languages if specified
    if args.all:
        args.python = args.all
        args.nodejs = args.all
        args.ruby = args.all
        args.go = args.all
        args.rust = args.all

    # Collect language strategies
    language_strategies: Dict[str, str] = {}
    if args.python:
        language_strategies["python"] = args.python
    if args.nodejs:
        language_strategies["nodejs"] = args.nodejs
    if args.ruby:
        language_strategies["ruby"] = args.ruby
    if args.go:
        language_strategies["go"] = args.go
    if args.rust:
        language_strategies["rust"] = args.rust

    if not language_strategies:
        parser.error("At least one language strategy must be specified")

    # Update the JSON file
    update_matrix_json(args.json_file, language_strategies, args.dry_run)


if __name__ == "__main__":
    main()
