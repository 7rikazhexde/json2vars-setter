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

# Stable .NET SDK tags look exactly like "v8.0.100"; pre-releases append a suffix
# (e.g. "v11.0.100-preview.4.26230.115", "v10.0.100-rc.1.25451.107").
_STABLE_TAG_PATTERN = re.compile(r"v\d+\.\d+\.\d+$")


class DotnetVersionFetcher(BaseVersionFetcher):
    """Fetches .NET SDK version information from GitHub"""

    def __init__(self) -> None:
        """Initialize with the .NET SDK GitHub repository information"""
        super().__init__("dotnet", "sdk")

    def _is_stable_tag(self, tag: JsonObject) -> bool:
        """
        Check if a tag represents a stable .NET SDK release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = str(tag.get("name", ""))

        # .NET SDK uses format "vX.Y.Z" for stable releases
        return bool(_STABLE_TAG_PATTERN.fullmatch(name))

    def _parse_version_from_tag(self, tag: JsonObject) -> ReleaseInfo:
        """
        Parse version information from a .NET SDK tag

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

        # Clean version string (e.g., "v8.0.100" -> "8.0.100")
        version = name.removeprefix("v")

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
        Determine the stable and latest versions of the .NET SDK

        Unlike most languages, the .NET SDK minor component is always ``0`` and the
        meaningful release line is the **major** version (8.0, 9.0, 10.0 ...), so:
        - latest: the most recent SDK release
        - stable: the newest SDK of the previous major version, when present

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
            major = int(match.group(1))
            # Look for the previous major version
            prev_major = major - 1

            # Search for the newest release with the previous major version
            for release in releases:
                r_match = re.match(r"(\d+)\.(\d+)\.(\d+)", release.version)
                if r_match and int(r_match.group(1)) == prev_major:
                    self.logger.info(
                        f"Using {release.version} as stable vs latest {latest_version}"
                    )
                    return latest, release

        # Use the latest version if no suitable stable version is found
        self.logger.info(
            f"No suitable stable version found, using latest {latest_version} as stable"
        )
        return latest, latest


def dotnet_filter_func(tag: JsonObject) -> bool:
    """Filter function for .NET SDK tags in API checker"""
    name = str(tag.get("name", ""))
    return bool(_STABLE_TAG_PATTERN.fullmatch(name))


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch .NET SDK version information")
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
            github_owner="dotnet",
            github_repo="sdk",
            count=args.count,
            filter_func=dotnet_filter_func,
        )

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching .NET SDK Versions ===")

    # Main processing
    fetcher = DotnetVersionFetcher()
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
