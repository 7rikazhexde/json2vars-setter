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

# The flutter/flutter GitHub tags are useless for "which Flutter SDK versions
# exist" (they return stale 1.x tags and are not newest-first). The official
# release manifest JSON on Google Cloud Storage is the authoritative source. The
# version numbers are platform-independent, so the Linux manifest is sufficient.
FLUTTER_RELEASES_URL = (
    "https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json"
)

# A stable Flutter version is a clean "X.Y.Z"; older hotfix forms such as
# "1.12.13+hotfix.9" are excluded by this anchored pattern.
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


class FlutterVersionFetcher(BaseVersionFetcher):
    """Fetches Flutter SDK version information from the official release manifest"""

    def __init__(self) -> None:
        """Initialize the fetcher.

        The base class wires up a requests session; the github owner/repo are
        unused because this fetcher overrides ``fetch_versions`` and talks to the
        Flutter release manifest (GCS) rather than the GitHub tags endpoint.
        """
        super().__init__("flutter", "flutter")

    def _is_stable_tag(self, tag: JsonObject) -> bool:
        """Not used: FlutterVersionFetcher uses the release manifest, not tags."""
        raise NotImplementedError(
            "FlutterVersionFetcher uses the release manifest, not tags"
        )

    def _parse_version_from_tag(self, tag: JsonObject) -> ReleaseInfo:
        """Not used: FlutterVersionFetcher uses the release manifest, not tags."""
        raise NotImplementedError(
            "FlutterVersionFetcher uses the release manifest, not tags"
        )

    def _list_stable_versions(self) -> List[str]:
        """
        List every stable Flutter SDK version from the release manifest.

        Filters the manifest's ``releases`` to the ``stable`` channel, keeps clean
        ``X.Y.Z`` versions, de-duplicates, and returns them sorted **numerically**,
        newest first.

        Returns:
            Stable version strings (e.g. ["3.44.2", "3.44.1", ...]), newest first
        """
        response = self.session.get(FLUTTER_RELEASES_URL, timeout=10)
        response.raise_for_status()
        data = cast(JsonObject, response.json())

        versions: List[str] = []
        seen = set()
        for release in cast(List[JsonObject], data.get("releases", [])):
            if release.get("channel") != "stable":
                continue
            version = str(release.get("version", ""))
            if _VERSION_RE.match(version) and version not in seen:
                seen.add(version)
                versions.append(version)

        # Sort numerically (major, minor, patch), newest first
        versions.sort(key=lambda v: tuple(int(p) for p in v.split(".")), reverse=True)
        return versions

    def _select_latest_stable(self, versions: List[str]) -> Tuple[str, str]:
        """
        Pick the latest version and a stable version from a newest-first list.

        - latest: the most recent version
        - stable: the newest release on the previous minor line (the previous
          distinct ``major.minor``). Flutter's stable minors are not contiguous
          (e.g. 3.41 then 3.44), so "previous minor" is found by scanning for a
          different line, not by subtracting 1.

        Args:
            versions: Stable versions, newest first

        Returns:
            Tuple of (latest, stable)

        Raises:
            ValueError: If the list is empty
        """
        if not versions:
            raise ValueError("No releases available")

        latest = versions[0]
        l_major, l_minor, _patch = (int(p) for p in latest.split("."))

        for version in versions:
            v_major, v_minor, _v_patch = (int(p) for p in version.split("."))
            if (v_major, v_minor) != (l_major, l_minor):
                self.logger.info(f"Using {version} as stable vs latest {latest}")
                return latest, version

        self.logger.info(
            f"No suitable stable version found, using latest {latest} as stable"
        )
        return latest, latest

    def fetch_versions(self, recent_count: int = 5) -> VersionInfo:
        """
        Fetch Flutter SDK version information from the official release manifest

        Args:
            recent_count: Number of recent stable releases to include

        Returns:
            VersionInfo object containing version information
        """
        try:
            versions = self._list_stable_versions()
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
                    "source": "flutter-releases:stable",
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
    parser = argparse.ArgumentParser(description="Fetch Flutter version information")
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
        print("\n=== Fetching Flutter Versions (release manifest) ===")

    # Main processing
    fetcher = FlutterVersionFetcher()
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
