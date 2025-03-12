import os
from typing import Any, Dict, List, Tuple

import requests

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import (
    ReleaseInfo,
    check_github_api,
    setup_logging,
)


class RustVersionFetcher(BaseVersionFetcher):
    """Fetches Rust version information from GitHub"""

    def __init__(self) -> None:
        """Initialize with Rust's GitHub repository information"""
        super().__init__("rust-lang", "rust")

    def _is_stable_tag(self, tag: Dict[str, Any]) -> bool:
        """
        Check if a tag represents a stable Rust release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = tag.get("name", "")

        # Rust uses format "1.xx.y" for stable releases
        return (
            name.startswith("1.")
            and len(name.split(".")) == 3
            and not any(
                x in name.lower()
                for x in ["beta", "alpha", "rc", "nightly", "dev", "test", "pre"]
            )
        )

    def _parse_version_from_tag(self, tag: Dict[str, Any]) -> ReleaseInfo:
        """
        Parse version information from a Rust tag

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

        # Version string is already in the correct format (e.g., "1.75.0")
        version = name.strip()

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

    def _get_additional_info(self) -> Dict[str, Any]:
        """
        Get additional Rust specific information (channel availability)

        Returns:
            Dictionary with Rust channel information
        """
        channel_info = self._fetch_rust_channel_info()
        return {"channel_info": channel_info}

    def _fetch_rust_channel_info(self) -> Dict[str, Any]:
        """
        Fetch Rust channel information from static.rust-lang.org

        Returns:
            Dictionary with channel information
        """
        try:
            # Check availability of the stable Rust channel
            stable_url = "https://static.rust-lang.org/dist/channel-rust-stable.toml"
            response = self.session.get(stable_url, timeout=10)

            # Just check response code for availability
            response.raise_for_status()

            return {"stable_channel_available": True}
        except Exception as e:
            self.logger.warning("Failed to fetch Rust channel information: %s", str(e))
            return {"stable_channel_available": False}

    def _get_stability_criteria(
        self, releases: List[ReleaseInfo]
    ) -> Tuple[ReleaseInfo, ReleaseInfo]:
        """
        Determine the stable and latest versions of Rust

        In Rust:
        - latest: the latest release version
        - stable: the release of the stable channel (usually the same as the latest)

        Args:
            releases: List of release information

        Returns:
            Tuple of (latest_release, stable_release)
        """
        if not releases:
            # In the original code, None, None was returned, but an exception is raised to pass type checking
            raise ValueError("No releases available")

        # The latest version is always the first release
        latest = releases[0]

        # In Rust, the latest release of the stable channel is usually the stable version
        # This is usually the same as the latest release
        stable = latest

        self.logger.info(
            f"For Rust, using latest {latest.version} as stable (stable channel)"
        )
        return latest, stable


def rust_filter_func(tag: Dict[str, Any]) -> bool:
    """Filter function for Rust tags in API checker"""
    name = tag.get("name", "")
    return (
        name.startswith("1.")
        and len(name.split(".")) == 3
        and not any(
            x in name.lower()
            for x in ["beta", "alpha", "rc", "nightly", "dev", "test", "pre"]
        )
    )


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch Rust version information")
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
            github_owner="rust-lang",
            github_repo="rust",
            count=args.count,
            filter_func=rust_filter_func,
        )

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching Rust Versions ===")

    # Main processing
    fetcher = RustVersionFetcher()
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
