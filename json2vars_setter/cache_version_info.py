#!/usr/bin/env python3
"""
Cache version information for programming languages.
This script fetches and caches version information for various programming languages.
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple

from json2vars_setter.version.core.base import BaseVersionFetcher, VersionInfo
from json2vars_setter.version.fetchers.go import GoVersionFetcher
from json2vars_setter.version.fetchers.nodejs import NodejsVersionFetcher
from json2vars_setter.version.fetchers.python import PythonVersionFetcher
from json2vars_setter.version.fetchers.ruby import RubyVersionFetcher
from json2vars_setter.version.fetchers.rust import RustVersionFetcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cache_version_info")

# Default paths
CACHE_DIR = Path(".github") / "workflows" / "cache"
DEFAULT_CACHE_FILE = CACHE_DIR / "version_cache.json"
DEFAULT_TEMPLATE_FILE = CACHE_DIR / "version_template.json"

# Default values for matrix.json
DEFAULT_OS = ["ubuntu-latest", "windows-latest", "macos-latest"]
DEFAULT_GHPAGES_BRANCH = "ghpages"


class VersionCache:
    """Handles caching of version information"""

    def __init__(self, cache_file: Path) -> None:
        """
        Initialize with the cache file path

        Args:
            cache_file: Path to the cache file
        """
        self.cache_file = cache_file
        self.data: Dict[str, Any] = self._load_cache()
        self.version_count: int = self._get_version_count()
        self.new_versions_found: DefaultDict[str, int] = defaultdict(
            int
        )  # Number of newly found versions

    def _load_cache(self) -> Dict[str, Any]:
        """
        Load the cache file if it exists

        Returns:
            Cache data structure
        """
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    data: Dict[str, Any] = json.load(f)
                return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load cache file: {e}")

        # Return empty cache structure if file doesn't exist or is invalid
        return {
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "version": "1.1",
            },
            "languages": {},
        }

    def _get_version_count(self) -> int:
        """Get the number of versions obtained"""
        if "metadata" in self.data and "version_count" in self.data["metadata"]:
            version_count: int = self.data["metadata"]["version_count"]
            return version_count
        return 0

    def save(self) -> None:
        """Save the cache to disk"""
        # Ensure cache directory exists
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.data, f, indent=4)
            logger.info(f"Cache saved to {self.cache_file}")
        except IOError as e:
            logger.error(f"Could not save cache: {e}")

    def is_update_needed(
        self, language: str, max_age_days: int = 1, requested_count: int = 0
    ) -> bool:
        """
        Check if the cached data for a language needs updating

        Args:
            language: The programming language to check
            max_age_days: Maximum age in days before cache is considered stale
            requested_count: Number of requested versions (if non-zero, compare with cached count)

        Returns:
            True if update is needed, False otherwise
        """
        # Update is needed if cache does not exist
        if "languages" not in self.data:
            logger.debug("Update needed because language cache does not exist")
            return True

        if language not in self.data.get("languages", {}):
            logger.debug(f"{language}: Update needed because cache does not exist")
            return True

        # Update is needed if there is no cache for the language
        language_info = self.data["languages"].get(language, {})
        if (
            not language_info
            or "recent_releases" not in language_info
            or not language_info["recent_releases"]
        ):
            logger.debug(
                f"{language}: Update needed because there is no release information"
            )
            return True

        # Update is needed if the number of requested versions is greater than the cached count
        if requested_count > 0:
            current_versions = len(
                self.data["languages"][language].get("recent_releases", [])
            )
            if current_versions < requested_count:
                logger.info(
                    f"{language}: Number of versions to fetch increased: {current_versions} → {requested_count}"
                )
                return True

        # Check the last update date
        last_updated = self.data["languages"][language].get("last_updated")
        if not last_updated:
            return True

        try:
            last_updated_dt = datetime.fromisoformat(last_updated)
            max_age = timedelta(days=max_age_days)
            is_stale = (datetime.utcnow() - last_updated_dt) > max_age
            if is_stale:
                logger.debug(
                    f"{language}: More than {max_age_days} days have passed since the last update"
                )
            return is_stale
        except (ValueError, TypeError):
            return True

    def merge_versions(
        self,
        language: str,
        version_info: VersionInfo,
        count: int = 0,
        incremental: bool = False,
    ) -> Tuple[bool, Set[str]]:
        """
        Update the cache for a language, optionally merging with existing data

        Args:
            language: The programming language to update
            version_info: The new version information to cache
            count: Number of versions obtained
            incremental: True if in incremental mode

        Returns:
            (Whether there were changes, Set of newly added versions)
        """
        if "languages" not in self.data:
            self.data["languages"] = {}

        if language not in self.data["languages"]:
            self.data["languages"][language] = {}

        # Get the existing version list
        existing_versions = set()
        existing_releases = []

        if incremental and "recent_releases" in self.data["languages"][language]:
            existing_releases = self.data["languages"][language]["recent_releases"]
            for release in existing_releases:
                if isinstance(release, dict) and "version" in release:
                    existing_versions.add(release["version"])

        # Serialize new release information
        new_releases = [vars(r) for r in version_info.recent_releases]

        # Track newly added versions
        new_versions = set()
        for release in new_releases:
            if release["version"] not in existing_versions:
                new_versions.add(release["version"])

        # Merge existing and new releases in incremental mode
        if incremental:
            # Add new releases to existing releases
            merged_releases = existing_releases.copy()

            # Add only versions that do not exist in the existing releases to avoid duplicates
            for release in new_releases:
                if release["version"] not in existing_versions:
                    merged_releases.append(release)

            # Sort by version (newest first) and keep the latest N releases
            if count > 0:
                merged_releases.sort(
                    key=lambda x: [
                        int(p) if p.isdigit() else p
                        for p in x["version"].replace("-", ".").split(".")
                    ],
                    reverse=True,
                )
                merged_releases = merged_releases[:count]
        else:
            # Use only new releases if not in incremental mode
            merged_releases = new_releases

        # Update latest and stable information
        latest = version_info.latest
        stable = version_info.stable

        # Maintain existing latest/stable if available and not obtained from API
        if latest is None and "latest" in self.data["languages"][language]:
            latest = self.data["languages"][language]["latest"]
            logger.debug(
                f"{language}: Maintained existing latest version as it was not obtained from API: {latest}"
            )

        if stable is None and "stable" in self.data["languages"][language]:
            stable = self.data["languages"][language]["stable"]
            logger.debug(
                f"{language}: Maintained existing stable version as it was not obtained from API: {stable}"
            )

        # Update cache
        self.data["languages"][language].update(
            {
                "latest": latest,
                "stable": stable,
                "recent_releases": merged_releases,
                "last_updated": datetime.utcnow().isoformat(),
            }
        )

        # Update metadata
        if "metadata" not in self.data:
            self.data["metadata"] = {}

        self.data["metadata"]["last_updated"] = datetime.utcnow().isoformat()

        # Update count information
        if count > 0:
            current_count = self.data["metadata"].get("version_count", 0)
            if count > current_count:
                self.data["metadata"]["version_count"] = count
                logger.debug(f"Updated version count: {current_count} → {count}")

        # Save the number of newly added versions
        self.new_versions_found[language] = len(new_versions)

        return bool(new_versions), new_versions


def get_version_fetcher(language: str) -> BaseVersionFetcher:
    """
    Get the appropriate version fetcher for the language

    Args:
        language: Programming language name

    Returns:
        Instantiated version fetcher for the specified language

    Raises:
        ValueError: If language is not supported
    """
    fetcher_classes = {
        "python": (PythonVersionFetcher, "python", "cpython"),
        "nodejs": (NodejsVersionFetcher, "nodejs", "node"),
        "ruby": (RubyVersionFetcher, "ruby", "ruby"),
        "go": (GoVersionFetcher, "golang", "go"),
        "rust": (RustVersionFetcher, "rust-lang", "rust"),
    }

    if language not in fetcher_classes:
        raise ValueError(f"Unsupported language: {language}")

    fetcher_class, owner, repo = fetcher_classes[language]
    return fetcher_class()


def update_versions(
    languages: List[str],
    force: bool = False,
    max_age_days: int = 1,
    count: int = 10,
    cache_file: Optional[Path] = None,
    incremental: bool = False,
) -> Dict[str, Any]:
    """
    Update version information for specified languages

    Args:
        languages: List of languages to update
        force: Force update even if cache is fresh
        max_age_days: Maximum age of cache in days
        count: Number of versions to fetch per language
        cache_file: Optional custom cache file path
        incremental: Whether to merge with existing cache

    Returns:
        Dictionary with version information and update summary
    """
    if not cache_file:
        cache_file = DEFAULT_CACHE_FILE

    cache = VersionCache(cache_file)

    # Track changes for reporting
    updated_languages = set()
    unchanged_languages = set()
    skipped_languages = set()
    failed_languages = set()
    new_versions = defaultdict(set)
    rate_limit_reached = False

    for language in languages:
        try:
            logger.info(f"Processing {language}...")

            # Skip if cache is fresh and force is False
            if not force and not cache.is_update_needed(language, max_age_days, count):
                logger.info(f"Cache for {language} is up to date, skipping")
                unchanged_languages.add(language)
                continue

            # Skip after reaching rate limit
            if rate_limit_reached:
                logger.warning(f"Skipping {language} due to previous rate limit errors")
                skipped_languages.add(language)
                continue

            # Fetch new version info
            fetcher = get_version_fetcher(language)
            version_info = fetcher.fetch_versions(recent_count=count)

            # Update cache with new info, possibly merging with existing data
            has_changes, new_version_set = cache.merge_versions(
                language, version_info, count, incremental
            )

            # Track version changes
            if has_changes:
                updated_languages.add(language)
                new_versions[language] = new_version_set
            else:
                unchanged_languages.add(language)

            # Report changes
            logger.info(
                f"Updated {language}: latest={version_info.latest}, stable={version_info.stable}"
            )
            if new_version_set:
                logger.info(
                    f"  Newly found versions: {', '.join(sorted(new_version_set, reverse=True))}"
                )

        except Exception as e:
            logger.error(f"Error updating {language}: {e}")
            failed_languages.add(language)

            # Check for rate limit errors
            if "rate limit exceeded" in str(e).lower():
                rate_limit_reached = True
                logger.warning(
                    "GitHub API rate limit reached. Consider using GITHUB_TOKEN environment variable."
                )

    # Save the cache
    cache.save()

    # Summary information
    result = {
        "updated": list(updated_languages),
        "unchanged": list(unchanged_languages),
        "skipped": list(skipped_languages),
        "failed": list(failed_languages),
        "new_versions_by_language": {
            lang: list(vers) for lang, vers in new_versions.items()
        },
        "cache_data": cache.data,
    }

    # Print summary
    logger.info("\n=== Summary ===")
    if updated_languages:
        logger.info(
            f"Updated ({len(updated_languages)}): {', '.join(updated_languages)}"
        )
    if unchanged_languages:
        logger.info(
            f"Unchanged ({len(unchanged_languages)}): {', '.join(unchanged_languages)}"
        )
    if skipped_languages:
        logger.info(
            f"Skipped due to rate limit ({len(skipped_languages)}): {', '.join(skipped_languages)}"
        )
    if failed_languages:
        logger.info(f"Failed ({len(failed_languages)}): {', '.join(failed_languages)}")

    if rate_limit_reached:
        logger.warning(
            "\nGitHub API rate limit was reached during processing. "
            "To increase limits, set the GITHUB_TOKEN environment variable:\n"
            "  export GITHUB_TOKEN=your_personal_access_token"
        )

    return result


def generate_version_template(
    cache_data: Dict[str, Any],
    output_file: Path,
    existing_file: Optional[Path] = None,
    languages: Optional[List[str]] = None,
    keep_existing: bool = True,
    sort_order: str = "desc",  # 'desc' or 'asc'
) -> None:
    """
    Generate a version template JSON file from the cache

    Args:
        cache_data: Cache data
        output_file: Path to write the template file
        existing_file: Path to an existing template file to maintain structure from
        languages: Optional list of languages to include (default: all cached languages)
        keep_existing: Maintain existing version information for languages not in cache
        sort_order: Version sort order - 'desc' (newest first) or 'asc' (oldest first)
    """
    # Start with default template
    template: Dict[str, Any] = {
        "os": DEFAULT_OS,
        "versions": {},
        "ghpages_branch": DEFAULT_GHPAGES_BRANCH,
    }

    # Load existing template if available
    existing_data: Dict[str, Any] = {}
    if existing_file and existing_file.exists():
        try:
            with open(existing_file, "r") as f:
                existing_data = json.load(f)

            # Preserve existing os and ghpages_branch if present
            if "os" in existing_data:
                template["os"] = existing_data["os"]
            if "ghpages_branch" in existing_data:
                template["ghpages_branch"] = existing_data["ghpages_branch"]

            logger.info(f"Maintained structure from existing file: {existing_file}")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing file: {e}")

    # Determine version sort order
    reverse_sort = sort_order.lower() == "desc"

    # Add versions for each language from cache
    for language, info in cache_data.get("languages", {}).items():
        # Skip if languages is specified and this language is not in the list
        if languages and language not in languages:
            continue

        if "recent_releases" in info and info["recent_releases"]:
            # Extract versions from recent releases, excluding prereleases
            versions: List[str] = []
            for release in info.get("recent_releases", []):
                if (
                    isinstance(release, dict)
                    and "version" in release
                    and not release.get("prerelease", False)
                ):
                    # Ensure version isn't already in the list
                    if release["version"] not in versions:
                        versions.append(release["version"])

            # Add stable and latest versions at the beginning
            if info.get("stable") and info["stable"] not in versions:
                versions.insert(0, info["stable"])
            if info.get("latest") and info["latest"] not in versions:
                # Avoid duplicates if latest is the same as stable
                if info.get("latest") != info.get("stable"):
                    versions.insert(0, info["latest"])

            # Sort supporting semantic versioning
            template["versions"][language] = sorted(
                list(set(versions)),
                reverse=reverse_sort,  # True for descending, False for ascending
                key=lambda v: [
                    int(p) if p.isdigit() else p for p in v.replace("-", ".").split(".")
                ],
            )

            logger.info(
                f"Added {language} versions to template ({len(versions)} versions, {sort_order} order)"
            )
        elif (
            keep_existing
            and existing_data
            and "versions" in existing_data
            and language in existing_data["versions"]
        ):
            # Maintain values from existing template
            template["versions"][language] = existing_data["versions"][language]
            logger.info(
                f"Maintained existing {language} versions ({len(existing_data['versions'][language])} versions)"
            )
        else:
            # Set empty list if no information
            template["versions"][language] = []
            logger.warning(f"No versions found for {language}")

    # Write template to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(template, f, indent=4)

    logger.info(f"Version template written to {output_file}")


def main() -> None:
    """Main function to parse arguments and update cache"""
    parser = argparse.ArgumentParser(
        description="""
Cache version information for programming languages.

This tool fetches version information from GitHub for various programming languages
and caches it locally for use in CI/CD workflows or other automation tasks.

Examples:
  # Update all languages with default settings
  python cache_version_info.py

  # Force update Python and Node.js with 20 versions each
  python cache_version_info.py --languages python nodejs --force --count 20

  # Update only when cache is older than 7 days
  python cache_version_info.py --max-age 7

  # Incrementally add new versions without replacing existing ones
  python cache_version_info.py --incremental

  # Only update the template from existing cache (no API calls)
  python cache_version_info.py --template-only

  # Only update the cache (no template generation)
  python cache_version_info.py --cache-only

  # Generate template with versions in ascending order (oldest first)
  python cache_version_info.py --sort asc
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        choices=["python", "nodejs", "ruby", "go", "rust", "all"],
        default=["all"],
        help="Languages to update (default: all)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force update even if cache is fresh"
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=1,
        help="Maximum age of cache in days before update (default: 1)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of versions to fetch per language (default: 10)",
    )
    parser.add_argument(
        "--cache-file",
        type=Path,
        default=DEFAULT_CACHE_FILE,
        help=f"Custom cache file path (default: {DEFAULT_CACHE_FILE})",
    )
    parser.add_argument(
        "--template-file",
        type=Path,
        default=DEFAULT_TEMPLATE_FILE,
        help=f"Path to write the template file (default: {DEFAULT_TEMPLATE_FILE})",
    )
    parser.add_argument(
        "--existing-template",
        type=Path,
        help="Path to an existing template file to maintain structure from",
    )
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Only update the cache, do not generate the template",
    )
    parser.add_argument(
        "--template-only",
        action="store_true",
        help="Only generate the template from existing cache (no API requests)",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Add only new versions without replacing existing cache",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Maintain existing version information when generating template",
    )
    parser.add_argument(
        "--sort",
        choices=["asc", "desc"],
        default="desc",
        help="Version sort order - desc: newest first (default), asc: oldest first",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Check for cache file existence
    if not args.template_only and not args.cache_file.exists():
        logger.warning(
            f"Cache file {args.cache_file} does not exist. Creating a new one."
        )
        # Force update if no cache exists
        force = True
    else:
        force = args.force

    # Expand "all" to all supported languages
    if "all" in args.languages:
        languages: List[str] = ["python", "nodejs", "ruby", "go", "rust"]
    else:
        languages = args.languages

    # Skip cache update in template-only mode
    cache_data: Optional[Dict[str, Any]] = None
    if not args.template_only:
        # Update versions
        result = update_versions(
            languages,
            force=force,  # Use variable instead of args.force
            max_age_days=args.max_age,
            count=args.count,
            cache_file=args.cache_file,
            incremental=args.incremental,
        )
        cache_data = result["cache_data"]
    else:
        logger.info("Template-only mode: Skipping cache update")
        # Load existing cache for template generation
        cache = VersionCache(args.cache_file)
        cache_data = cache.data

    # Skip template generation in cache-only mode
    if not args.cache_only and cache_data:
        # Generate template file
        generate_version_template(
            cache_data,
            args.template_file,
            args.existing_template or args.template_file,
            languages
            if not args.template_only or "all" not in args.languages
            else None,
            args.keep_existing,
            args.sort,  # Pass sort order
        )
    elif args.cache_only:
        logger.info("Cache-only mode: Skipping template generation")

    logger.info("Processing completed")


if __name__ == "__main__":
    main()
