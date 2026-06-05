from typing import List, cast

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.utils import (
    JsonObject,
    ReleaseInfo,
    VersionInfo,
    get_utc_now,
    setup_logging,
)

# Java (OpenJDK) GA/LTS releases are not cleanly represented by a single GitHub
# repository's tags (openjdk/jdk only carries early-access builds of the in-development
# release, and GA/LTS lines live in separate update repositories). The Adoptium API
# is the authoritative, clean source for "which Java versions are available".
ADOPTIUM_API_BASE = "https://api.adoptium.net/v3"


class JavaVersionFetcher(BaseVersionFetcher):
    """Fetches Java (Temurin/Adoptium) version information from the Adoptium API"""

    def __init__(self) -> None:
        """Initialize with the Adoptium API endpoint"""
        # The base class wires up an authenticated requests session; the github
        # owner/repo are unused because this fetcher overrides ``fetch_versions``
        # and talks to the Adoptium API rather than the GitHub tags endpoint.
        super().__init__("adoptium", "temurin")
        self.available_releases_url = f"{ADOPTIUM_API_BASE}/info/available_releases"

    def _is_stable_tag(self, tag: JsonObject) -> bool:
        """Not used: JavaVersionFetcher uses the Adoptium API, not GitHub tags."""
        raise NotImplementedError("JavaVersionFetcher uses the Adoptium API, not tags")

    def _parse_version_from_tag(self, tag: JsonObject) -> ReleaseInfo:
        """Not used: JavaVersionFetcher uses the Adoptium API, not GitHub tags."""
        raise NotImplementedError("JavaVersionFetcher uses the Adoptium API, not tags")

    def fetch_versions(self, recent_count: int = 5) -> VersionInfo:
        """
        Fetch Java version information from the Adoptium API

        - latest: the most recent feature release (e.g. 26)
        - stable: the most recent LTS release (e.g. 25)
        - recent_releases: the available LTS releases, newest first

        Args:
            recent_count: Maximum number of LTS releases to include

        Returns:
            VersionInfo object containing version information
        """
        try:
            response = self.session.get(self.available_releases_url, timeout=10)
            response.raise_for_status()
            data = cast(JsonObject, response.json())

            # LTS releases are the meaningful axis for a Java CI matrix
            lts_raw = cast(List[object], data.get("available_lts_releases", []))
            lts_sorted = sorted((int(str(v)) for v in lts_raw), reverse=True)

            most_recent_feature = data.get("most_recent_feature_release")
            most_recent_lts = data.get("most_recent_lts")

            recent_releases = [
                ReleaseInfo(version=str(v), prerelease=False)
                for v in lts_sorted[:recent_count]
            ]

            latest = (
                str(most_recent_feature) if most_recent_feature is not None else None
            )
            stable = str(most_recent_lts) if most_recent_lts is not None else None

            return VersionInfo(
                latest=latest,
                stable=stable,
                recent_releases=recent_releases,
                details={
                    "fetch_time": get_utc_now().isoformat(),
                    "source": "adoptium:info/available_releases",
                    "most_recent_feature_release": most_recent_feature,
                    "most_recent_lts": most_recent_lts,
                    "available_lts_releases": lts_sorted,
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
    parser = argparse.ArgumentParser(description="Fetch Java version information")
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
        print("\n=== Fetching Java Versions (Adoptium API) ===")

    # Main processing
    fetcher = JavaVersionFetcher()
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
