import os
import re
from typing import List, Optional, Tuple, cast

import requests

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import (
    JsonObject,
    ReleaseInfo,
    check_github_api,
    setup_logging,
)

# Final GCC releases are tagged "releases/gcc-X.Y.Z"; the X.Y.Z version is
# captured. Other tags in the repo — "releases/libgcj-*", "releases/libf2c-*",
# "vendors/ARM/*", "basepoints/*" and the like — do not match and are excluded.
_STABLE_TAG_PATTERN = re.compile(r"releases/gcc-(\d+\.\d+\.\d+)$")


class GccVersionFetcher(BaseVersionFetcher):
    """Fetches GCC version information from GitHub (gcc-mirror/gcc)"""

    def __init__(self) -> None:
        """Initialize with GCC's GitHub repository information"""
        super().__init__("gcc-mirror", "gcc")

    def _is_stable_tag(self, tag: JsonObject) -> bool:
        """
        Check if a tag represents a stable GCC release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = str(tag.get("name", ""))

        # GCC uses "releases/gcc-X.Y.Z" for final releases
        return bool(_STABLE_TAG_PATTERN.fullmatch(name))

    def _parse_version_from_tag(self, tag: JsonObject) -> ReleaseInfo:
        """
        Parse version information from a GCC tag

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

        # Extract version from the tag (e.g., "releases/gcc-15.1.0" -> "15.1.0")
        match = _STABLE_TAG_PATTERN.fullmatch(name)
        if not match:
            raise ParseError(f"Could not parse version from tag: {name}")
        version = match.group(1)

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

    def _version_sort_key(self, tag: JsonObject) -> Tuple[int, int, int]:
        """
        Build a numeric (major, minor, patch) sort key for a stable tag.

        Only tags that already passed ``_is_stable_tag`` reach this method, so
        ``_parse_version_from_tag`` always yields a clean "X.Y.Z" version.
        """
        version = self._parse_version_from_tag(tag).version
        major, minor, patch = (int(part) for part in version.split("."))
        return (major, minor, patch)

    def _get_github_tags(self, count: Optional[int] = None) -> List[JsonObject]:
        """
        Fetch stable tags and return the newest ``count`` ordered by version.

        The gcc-mirror/gcc tag list interleaves release tags with "libgcj-*",
        "libf2c-*", "vendors/*" and "basepoints/*" tags and is not reliably
        newest-first, so fetch a generous set of release tags and sort them by
        semantic version before truncating; this guarantees
        ``_get_stability_criteria`` sees the real latest release.
        """
        target = count if count is not None else 5
        tags = super()._get_github_tags(count=100)
        tags.sort(key=self._version_sort_key, reverse=True)
        return tags[:target]

    def _get_stability_criteria(
        self, releases: List[ReleaseInfo]
    ) -> Tuple[ReleaseInfo, ReleaseInfo]:
        """
        Determine the stable and latest versions of GCC

        - latest: the most recent release version
        - stable: the newest release from the previous **major series**. GCC's
          release series is its major number (15.1.0 / 15.2.0 / 15.3.0 are all
          "GCC 15"), so the previous line is the previous major, not the previous
          minor.

        Args:
            releases: List of release information (sorted newest-first)

        Returns:
            Tuple of (latest_release, stable_release)
        """
        if not releases:
            # Raise an exception to explicitly handle the empty case
            raise ValueError("No releases available")

        # The latest version is always the first (highest) release
        latest = releases[0]

        match = re.match(r"(\d+)\.(\d+)\.(\d+)", latest.version)
        if match:
            major = int(match.group(1))

            # Find the newest release on a different major series
            for release in releases:
                r_match = re.match(r"(\d+)\.(\d+)\.(\d+)", release.version)
                if r_match:
                    r_major = int(r_match.group(1))
                    if r_major != major:
                        self.logger.info(
                            f"Using {release.version} as stable vs latest {latest.version}"
                        )
                        return latest, release

        # Use the latest version if no suitable stable version is found
        self.logger.info(
            f"No suitable stable version found, using latest {latest.version} as stable"
        )
        return latest, latest


def gcc_filter_func(tag: JsonObject) -> bool:
    """Filter function for GCC tags in API checker"""
    name = str(tag.get("name", ""))
    return bool(_STABLE_TAG_PATTERN.fullmatch(name))


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch GCC version information")
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
            github_owner="gcc-mirror",
            github_repo="gcc",
            count=args.count,
            filter_func=gcc_filter_func,
        )

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching GCC Versions ===")

    # Main processing
    fetcher = GccVersionFetcher()
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
