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

# Final GHC releases are tagged "ghc-X.Y.Z-release"; the X.Y.Z version is
# captured. Pre-releases ("ghc-9.14.1-rc1", "ghc-9.14.1-alpha1"), branch markers
# ("ghc-9.15-start") and "wip/*" tags do not match and are excluded.
_STABLE_TAG_PATTERN = re.compile(r"ghc-(\d+\.\d+\.\d+)-release$")


class HaskellVersionFetcher(BaseVersionFetcher):
    """Fetches Haskell (GHC) version information from GitHub"""

    def __init__(self) -> None:
        """Initialize with GHC's GitHub repository information"""
        super().__init__("ghc", "ghc")

    def _is_stable_tag(self, tag: JsonObject) -> bool:
        """
        Check if a tag represents a stable GHC release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = str(tag.get("name", ""))

        # GHC uses "ghc-X.Y.Z-release" for final releases
        return bool(_STABLE_TAG_PATTERN.fullmatch(name))

    def _parse_version_from_tag(self, tag: JsonObject) -> ReleaseInfo:
        """
        Parse version information from a GHC tag

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

        # Extract version from the tag (e.g., "ghc-9.10.1-release" -> "9.10.1")
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

        The ghc/ghc tag list is dominated by pre-release / branch-marker / "wip"
        tags and is not newest-first, so fetch a generous set of release tags and
        sort them by semantic version before truncating; this guarantees
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
        Determine the stable and latest versions of GHC

        - latest: the most recent release version
        - stable: the newest release from the previous minor line (GHC ships only
          even minor lines, so "previous minor" is found by version, not minor-1)

        Args:
            releases: List of release information (sorted newest-first)

        Returns:
            Tuple of (latest_release, stable_release)
        """
        if not releases:
            # Raise an exception to explicitly handle the case where no releases are available
            raise ValueError("No releases available")

        # The latest version is always the first (highest) release
        latest = releases[0]

        # Get and parse the version number
        latest_version = latest.version
        match = re.match(r"(\d+)\.(\d+)\.(\d+)", latest_version)

        if match:
            major, minor, _patch = map(int, match.groups())

            # Search for the newest release on a different minor line
            for release in releases:
                r_match = re.match(r"(\d+)\.(\d+)\.(\d+)", release.version)
                if r_match:
                    r_major, r_minor, _r_patch = map(int, r_match.groups())
                    if (r_major, r_minor) != (major, minor):
                        self.logger.info(
                            f"Using {release.version} as stable vs latest {latest_version}"
                        )
                        return latest, release

        # Use the latest version if no suitable stable version is found
        self.logger.info(
            f"No suitable stable version found, using latest {latest_version} as stable"
        )
        return latest, latest


def haskell_filter_func(tag: JsonObject) -> bool:
    """Filter function for Haskell (GHC) tags in API checker"""
    name = str(tag.get("name", ""))
    return bool(_STABLE_TAG_PATTERN.fullmatch(name))


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Fetch Haskell (GHC) version information"
    )
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
            github_owner="ghc",
            github_repo="ghc",
            count=args.count,
            filter_func=haskell_filter_func,
        )

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching Haskell (GHC) Versions ===")

    # Main processing
    fetcher = HaskellVersionFetcher()
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
