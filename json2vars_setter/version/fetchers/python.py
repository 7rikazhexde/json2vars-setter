import os
import re
from typing import Any, Dict, List, Tuple

import requests

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import (
    ReleaseInfo,
    check_github_api,
    setup_logging,
)


class PythonVersionFetcher(BaseVersionFetcher):
    """Fetches Python version information from GitHub"""

    def __init__(self) -> None:
        """Initialize with Python's GitHub repository information"""
        super().__init__("python", "cpython")

    def _is_stable_tag(self, tag: Dict[str, Any]) -> bool:
        """
        Check if a tag represents a stable Python release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = tag.get("name", "")

        # Python uses format "vX.Y.Z" for stable releases (3.x and 4.x series)
        return name.startswith(("v3", "v4")) and not any(
            x in name.lower()
            for x in [
                "a",
                "rc",
                "b",
                "beta",
                "alpha",
                "pre",
                "preview",
                "dev",
                "test",
                "nightly",
                "snapshot",
            ]
        )

    def _parse_version_from_tag(self, tag: Dict[str, Any]) -> ReleaseInfo:
        """
        Parse version information from a Python tag

        Args:
            tag: Tag information from GitHub API

        Returns:
            Parsed ReleaseInfo object

        Raises:
            ParseError: If required version information cannot be parsed
        """
        name = tag.get("name", "")
        if not name:
            raise ParseError("No tag name found")

        # Clean version string (e.g., "v3.12.0" -> "3.12.0")
        version = name.lstrip("v")

        # All filtered tags are considered stable
        prerelease = False

        return ReleaseInfo(
            version=version,
            release_date=None,
            prerelease=prerelease,
            additional_info={
                "tag_name": name,
                "commit": {"sha": tag.get("commit", {}).get("sha")},
                "tarball_url": tag.get("tarball_url"),
                "zipball_url": tag.get("zipball_url"),
            },
        )

    def _get_stability_criteria(
        self, releases: List[ReleaseInfo]
    ) -> Tuple[ReleaseInfo, ReleaseInfo]:
        """
        Determine the stable and latest versions of Python

        In Python:
        - latest: The most recent release version
        - stable: Typically the widely adopted version (one minor version behind)
          or explicitly marked as "stable"

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
            major, minor, patch = map(int, match.groups())
            # Look for the previous minor version
            prev_minor = minor - 1

            # Search for the release with the previous minor version
            for release in releases:
                r_match = re.match(r"(\d+)\.(\d+)\.(\d+)", release.version)
                if r_match:
                    r_major, r_minor, r_patch = map(int, r_match.groups())
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


def python_filter_func(tag: Dict[str, Any]) -> bool:
    """Filter function for Python tags in API checker"""
    name = tag.get("name", "")

    # Regular expression pattern to fully detect keywords indicating unstable versions
    unstable_pattern = r"(a|rc|b|beta|alpha|pre|preview|dev|test|nightly|snapshot)"

    # The tag should start with v3 or v4 and not contain unstable keywords
    return (
        name.startswith(("v3", "v4"))
        and
        # Use regular expressions to check for exact keyword matches
        not re.search(rf"\d+\.{unstable_pattern}", name.lower())
        and not re.search(rf"{unstable_pattern}", name.lower())
    )


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch Python version information")
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
            github_owner="python",
            github_repo="cpython",
            count=args.count,
            filter_func=python_filter_func,
        )

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching Python Versions ===")

    # Main processing
    fetcher = PythonVersionFetcher()
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
