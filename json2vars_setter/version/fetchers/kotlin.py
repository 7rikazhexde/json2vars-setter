import os
import re
from typing import List, Optional, Tuple, cast

import requests

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo, setup_logging

# A stable Kotlin tag is exactly "vX.Y.Z" with no suffix. Pre-releases carry a
# suffix (e.g. "v2.4.0-RC2", "v2.4.0-Beta1", older "v1.9.0-M1"), which this
# anchored pattern rejects.
_STABLE_TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")


class KotlinVersionFetcher(BaseVersionFetcher):
    """Fetches Kotlin version information from GitHub (JetBrains/kotlin)"""

    def __init__(self) -> None:
        """Initialize with Kotlin's GitHub repository information"""
        super().__init__("JetBrains", "kotlin")

    def _is_stable_tag(self, tag: JsonObject) -> bool:
        """
        Check if a tag represents a stable Kotlin release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = str(tag.get("name", ""))

        # Kotlin uses "vX.Y.Z" for stable releases; pre-releases add a suffix
        # such as "-RC", "-RC2", "-Beta1", "-M1" which the anchored regex rejects.
        return bool(_STABLE_TAG_RE.match(name))

    def _parse_version_from_tag(self, tag: JsonObject) -> ReleaseInfo:
        """
        Parse version information from a Kotlin tag

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

        # Clean version string (e.g., "v2.4.0" -> "2.4.0")
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
        Determine the stable and latest versions of Kotlin

        In Kotlin:
        - latest: The most recent release version
        - stable: Usually the previous minor version to the latest

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

            # Search for the release with the previous minor version
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

    url = "https://api.github.com/repos/JetBrains/kotlin/tags"
    print("\n=== Checking GitHub API ===")
    print("Checking JetBrains/kotlin tags...")

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
    parser = argparse.ArgumentParser(description="Fetch Kotlin version information")
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
        print("\n=== Fetching Kotlin Versions ===")

    # Main processing
    fetcher = KotlinVersionFetcher()
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
