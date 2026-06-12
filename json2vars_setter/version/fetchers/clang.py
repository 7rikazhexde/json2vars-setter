import os
import re
from typing import List, Optional, Tuple, cast

import requests

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo, setup_logging

# A stable Clang/LLVM tag is exactly "llvmorg-X.Y.Z" with no suffix. Release
# candidates carry a "-rcN" suffix (e.g. "llvmorg-22.1.0-rc3") and each dev cycle
# opens with a non-release "llvmorg-NN-init" tag; this anchored pattern rejects both.
_STABLE_TAG_RE = re.compile(r"^llvmorg-\d+\.\d+\.\d+$")


class ClangVersionFetcher(BaseVersionFetcher):
    """Fetches Clang/LLVM version information from GitHub (llvm/llvm-project)"""

    def __init__(self) -> None:
        """Initialize with the LLVM project's GitHub repository information"""
        super().__init__("llvm", "llvm-project")

    def _is_stable_tag(self, tag: JsonObject) -> bool:
        """
        Check if a tag represents a stable Clang/LLVM release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = str(tag.get("name", ""))

        # LLVM uses "llvmorg-X.Y.Z" for stable releases; "-rcN" and "NN-init"
        # tags are rejected by the anchored regex.
        return bool(_STABLE_TAG_RE.match(name))

    def _parse_version_from_tag(self, tag: JsonObject) -> ReleaseInfo:
        """
        Parse version information from a Clang/LLVM tag

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

        # Clean version string (e.g., "llvmorg-22.1.7" -> "22.1.7")
        version = name.removeprefix("llvmorg-")

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
        Determine the stable and latest versions of Clang/LLVM

        In LLVM:
        - latest: the most recent release version
        - stable: the newest release on the previous version line (the previous
          distinct major.minor). LLVM bumps the major roughly yearly while the
          minor is almost always 1 (e.g. 22.1.x follows 21.1.x), so "previous
          minor" is not meaningful — the previous *line* is what users pin against.

        Args:
            releases: List of release information

        Returns:
            Tuple of (latest_release, stable_release)
        """
        if not releases:
            # Raise an exception to explicitly handle the empty case
            raise ValueError("No releases available")

        # The latest version is always the first release
        latest = releases[0]

        match = re.match(r"(\d+)\.(\d+)\.(\d+)", latest.version)
        if match:
            major, minor, _patch = map(int, match.groups())

            # Find the newest release on a different major.minor line
            for release in releases:
                r_match = re.match(r"(\d+)\.(\d+)\.(\d+)", release.version)
                if r_match:
                    r_major, r_minor, _r_patch = map(int, r_match.groups())
                    if (r_major, r_minor) != (major, minor):
                        self.logger.info(
                            f"Using {release.version} as stable vs latest {latest.version}"
                        )
                        return latest, release

        # Use the latest version if no suitable stable version is found
        self.logger.info(
            f"No suitable stable version found, using latest {latest.version} as stable"
        )
        return latest, latest


# Custom function to check the API directly
def check_api(
    session: requests.Session, count: Optional[int] = None, verbose: int = 0
) -> None:
    """
    Check tags directly from GitHub (supports multiple pages)

    Args:
        session: Requests session to use
        count: Optional number of tags to display
        verbose: Verbosity level (0: off, 1: basic, 2: detailed)
    """
    if not verbose:
        return

    count = count or 5  # Set default value
    stable_tags: List[JsonObject] = []
    page = 1
    max_pages = 3  # Check up to 3 pages

    url = "https://api.github.com/repos/llvm/llvm-project/tags"
    print("\n=== Checking GitHub API ===")
    print("Checking llvm/llvm-project tags...")

    while len(stable_tags) < count and page <= max_pages:
        try:
            params = {"page": page, "per_page": 100}
            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()
            tags = response.json()

            if page == 1:  # Display information only for the first page
                print("Status Code: {}".format(response.status_code))
                print(f"Checking page {page}...")

                if verbose > 1 and tags:
                    print("\nFirst 5 raw tags on page 1:")
                    for tag in tags[:5]:
                        print(f"- {tag.get('name')}")

            if not tags:
                break

            # Filter only stable tags
            new_stable_tags = [
                tag for tag in tags if _STABLE_TAG_RE.match(str(tag.get("name", "")))
            ]

            print(f"Found {len(new_stable_tags)} stable tags on page {page}")
            stable_tags.extend(new_stable_tags)

            if len(tags) < 100:  # Last page
                break

            page += 1

        except Exception as e:
            print("Error: {}".format(str(e)))
            break

    print("\nTotal stable tags found: {}".format(len(stable_tags)))

    if stable_tags:
        print("\nRecent stable version tags (max {}):".format(count))
        for tag in stable_tags[:count]:
            print("- {}".format(tag["name"]))


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch Clang/LLVM version information")
    parser.add_argument(
        "--count", type=int, default=5, help="Number of versions to fetch"
    )
    parser.add_argument(
        "--verbose", "-v", action="count", default=0, help="Increase verbosity"
    )
    args = parser.parse_args()

    # Set up logging
    logger = setup_logging(args.verbose)

    # Check API directly using the improved check_api function
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

        # Use the improved check_api function
        check_api(session=session, count=args.count, verbose=args.verbose)

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching Clang/LLVM Versions ===")

    # Main processing
    fetcher = ClangVersionFetcher()
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
