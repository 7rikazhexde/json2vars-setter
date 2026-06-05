import os
import re
from typing import List, Tuple, cast

import requests

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import (
    JsonObject,
    ReleaseInfo,
    check_github_api,
    setup_logging,
)

# Stable PHP tags look exactly like "php-8.4.1"; pre-releases append a suffix
# (e.g. "php-8.5.0RC1", "php-8.5.0beta1") and unrelated tags (e.g. "yaf-2.1.0")
# do not match this pattern.
_STABLE_TAG_PATTERN = re.compile(r"php-\d+\.\d+\.\d+$")


class PhpVersionFetcher(BaseVersionFetcher):
    """Fetches PHP version information from GitHub"""

    def __init__(self) -> None:
        """Initialize with PHP's GitHub repository information"""
        super().__init__("php", "php-src")

    def _is_stable_tag(self, tag: JsonObject) -> bool:
        """
        Check if a tag represents a stable PHP release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = str(tag.get("name", ""))

        # PHP uses format "php-X.Y.Z" for stable releases
        return bool(_STABLE_TAG_PATTERN.fullmatch(name))

    def _parse_version_from_tag(self, tag: JsonObject) -> ReleaseInfo:
        """
        Parse version information from a PHP tag

        Args:
            tag: Tag information from GitHub API

        Returns:
            Parsed ReleaseInfo object

        Raises:
            ParseError: If required version information cannot be parsed
        """
        name = str(tag.get("name", ""))
        if not name:
            raise ParseError("No tag name found")

        # Clean version string (e.g., "php-8.4.1" -> "8.4.1")
        version = name.removeprefix("php-")

        # All filtered tags are considered stable
        prerelease = False

        return ReleaseInfo(
            version=version,
            release_date=None,
            prerelease=prerelease,
            additional_info={
                "tag_name": name,
                "commit": {"sha": cast(JsonObject, tag.get("commit", {})).get("sha")},
                "tarball_url": tag.get("tarball_url"),
                "zipball_url": tag.get("zipball_url"),
            },
        )

    def _get_stability_criteria(
        self, releases: List[ReleaseInfo]
    ) -> Tuple[ReleaseInfo, ReleaseInfo]:
        """
        Determine the stable and latest versions of PHP

        In PHP:
        - latest: The most recent release version
        - stable: Usually the previous minor version to the latest, or
          a version that has been stable for a sufficient period

        Args:
            releases: List of release information

        Returns:
            Tuple of (latest_release, stable_release)
        """
        if not releases:
            # Raise an exception to explicitly handle the case where no releases are available
            raise ValueError("No releases available")

        # The latest version is always the first release
        latest = releases[0]

        # Get and parse the version number
        latest_version = latest.version
        match = re.match(r"(\d+)\.(\d+)\.(\d+)", latest_version)

        if match:
            major, minor, _patch = map(int, match.groups())
            # Look for the previous minor version
            prev_minor = minor - 1

            # Search for a release with the previous minor version
            for release in releases:
                r_match = re.match(r"(\d+)\.(\d+)\.(\d+)", release.version)
                if r_match:
                    r_major, r_minor, _r_patch = map(int, r_match.groups())
                    if r_major == major and r_minor == prev_minor:
                        self.logger.info(
                            f"Using {release.version} as stable vs latest {latest_version}"
                        )
                        return latest, release

        # Use the latest version if no suitable stable version is found
        self.logger.info(
            f"No suitable stable version found, using latest {latest_version} as stable"
        )
        return latest, latest


def php_filter_func(tag: JsonObject) -> bool:
    """Filter function for PHP tags in API checker"""
    name = str(tag.get("name", ""))
    return bool(_STABLE_TAG_PATTERN.fullmatch(name))


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch PHP version information")
    parser.add_argument(
        "--count", type=int, default=5, help="Number of versions to fetch"
    )
    parser.add_argument(
        "--verbose", "-v", action="count", default=0, help="Increase verbosity"
    )
    args = parser.parse_args()

    # Set up logging
    logger = setup_logging(args.verbose)

    # Check API directly if in verbose mode
    if args.verbose > 0:
        # Create a session for API checking
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "json2vars-setter",
            }
        )

        # Add GitHub token if available
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            session.headers.update({"Authorization": f"token {github_token}"})

        check_github_api(
            session=session,
            github_owner="php",
            github_repo="php-src",
            count=args.count,
            filter_func=php_filter_func,
        )

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching PHP Versions ===")

    # Main processing
    fetcher = PhpVersionFetcher()
    versions = fetcher.fetch_versions(recent_count=args.count)

    # Output results
    print(
        json.dumps(
            {
                "latest": versions.latest,
                "stable": versions.stable,
                "recent_releases": [vars(r) for r in versions.recent_releases],
                "details": versions.details,
            },
            indent=2,
        )
    )
