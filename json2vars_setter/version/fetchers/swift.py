import re
from typing import List, Tuple, cast

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.utils import (
    JsonObject,
    ReleaseInfo,
    VersionInfo,
    get_utc_now,
    setup_logging,
)

# Swift release versions are not cleanly represented by the apple/swift GitHub tags
# (that repository is dominated by DEVELOPMENT-SNAPSHOT tags and the
# ``swift-X.Y.Z-RELEASE`` tags do not appear within the first pages of the tags
# listing). The official swift.org install API is the authoritative, clean source.
SWIFT_RELEASES_URL = "https://www.swift.org/api/v1/install/releases.json"

# Release names look like "6.3.2" or "6.2" (major.minor[.patch]); anything else
# (snapshots, etc.) is ignored.
_VERSION_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")


def _version_key(version: str) -> Tuple[int, int, int]:
    """Return a numeric sort key for a major.minor[.patch] version string."""
    parts = [int(p) for p in version.split(".")]
    while len(parts) < 3:
        parts.append(0)
    return parts[0], parts[1], parts[2]


class SwiftVersionFetcher(BaseVersionFetcher):
    """Fetches Swift version information from the swift.org install API"""

    def __init__(self) -> None:
        """Initialize the fetcher.

        The base class wires up a requests session; the github owner/repo are
        unused because this fetcher overrides ``fetch_versions`` and talks to the
        swift.org install API rather than the GitHub tags endpoint.
        """
        super().__init__("apple", "swift")

    def _is_stable_tag(self, tag: JsonObject) -> bool:
        """Not used: SwiftVersionFetcher uses the swift.org API, not GitHub tags."""
        raise NotImplementedError(
            "SwiftVersionFetcher uses the swift.org API, not tags"
        )

    def _parse_version_from_tag(self, tag: JsonObject) -> ReleaseInfo:
        """Not used: SwiftVersionFetcher uses the swift.org API, not GitHub tags."""
        raise NotImplementedError(
            "SwiftVersionFetcher uses the swift.org API, not tags"
        )

    def _list_release_versions(self) -> List[str]:
        """
        List every stable Swift release version from the swift.org install API.

        Returns:
            Version strings (e.g. ["6.3.2", "6.3.1", ...]), newest first
        """
        response = self.session.get(SWIFT_RELEASES_URL, timeout=10)
        response.raise_for_status()
        data = cast(List[JsonObject], response.json())

        versions = [
            name
            for entry in data
            if _VERSION_RE.match(name := str(entry.get("name", "")))
        ]

        versions.sort(key=_version_key, reverse=True)
        return versions

    def _select_latest_stable(self, versions: List[str]) -> Tuple[str, str]:
        """
        Pick the latest version and a stable version from a newest-first list.

        - latest: the most recent version
        - stable: the newest release of the previous minor of latest (falls back
          to latest when no previous-minor release is available)

        Args:
            versions: Versions, newest first

        Returns:
            Tuple of (latest, stable)

        Raises:
            ValueError: If the list is empty
        """
        if not versions:
            raise ValueError("No releases available")

        latest = versions[0]
        major, minor, _patch = _version_key(latest)
        prev_minor = minor - 1

        for version in versions:
            v_major, v_minor, _v_patch = _version_key(version)
            if v_major == major and v_minor == prev_minor:
                self.logger.info(f"Using {version} as stable vs latest {latest}")
                return latest, version

        self.logger.info(
            f"No suitable stable version found, using latest {latest} as stable"
        )
        return latest, latest

    def fetch_versions(self, recent_count: int = 5) -> VersionInfo:
        """
        Fetch Swift version information from the swift.org install API

        Args:
            recent_count: Number of recent stable releases to include

        Returns:
            VersionInfo object containing version information
        """
        try:
            versions = self._list_release_versions()
            if not versions:
                return VersionInfo(details={"error": "No releases found"})

            latest, stable = self._select_latest_stable(versions)

            recent_releases = [
                ReleaseInfo(version=v, prerelease=False)
                for v in versions[:recent_count]
            ]

            return VersionInfo(
                latest=latest,
                stable=stable,
                recent_releases=recent_releases,
                details={
                    "fetch_time": get_utc_now().isoformat(),
                    "source": "swift.org:install/releases",
                    "latest": latest,
                    "stable": stable,
                },
            )
        except Exception as error:
            self.logger.error("Error fetching versions: %s", str(error), exc_info=True)
            return VersionInfo(
                details={"error": str(error), "error_type": type(error).__name__}
            )


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch Swift version information")
    parser.add_argument(
        "--count", type=int, default=5, help="Number of versions to fetch"
    )
    parser.add_argument(
        "--verbose", "-v", action="count", default=0, help="Increase verbosity"
    )
    args = parser.parse_args()

    # Set up logging
    logger = setup_logging(args.verbose)

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching Swift Versions (swift.org) ===")

    # Main processing
    fetcher = SwiftVersionFetcher()
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
