import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests


@dataclass
class VersionInfo:
    latest: Optional[str] = None
    stable: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.details is None:
            self.details = {}


def fetch_python_versions() -> VersionInfo:
    """Fetch Python versions."""
    try:
        session = requests.Session()
        url = "https://www.python.org/api/v2/downloads/release/?is_published=true"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        releases = response.json()

        result = VersionInfo(
            details={"source": url, "fetch_time": response.headers.get("date")}
        )

        versions = []
        for release in releases:
            if release.get("is_published"):
                version_str = str(release.get("name", "")).replace("Python ", "")
                versions.append(
                    {
                        "version": version_str,
                        "date": release.get("release_date", ""),
                        "is_stable": not any(
                            x in version_str.lower() for x in ["a", "b", "rc"]
                        ),
                    }
                )

        # Sort by release date (newest first)
        versions.sort(key=lambda x: x["date"], reverse=True)

        if versions:
            # Latest version (including pre-releases)
            result.latest = versions[0]["version"]
            result.details["latest_info"] = versions[0]

            # Latest stable version
            stable = next((v for v in versions if v["is_stable"]), None)
            if stable:
                result.stable = stable["version"]
                result.details["stable_info"] = stable

        return result

    except Exception as e:
        return VersionInfo(details={"error": str(e)})


if __name__ == "__main__":
    versions = fetch_python_versions()
    print("\n=== Python Versions ===")
    print(
        json.dumps(
            {
                "latest": versions.latest,
                "stable": versions.stable,
                "details": versions.details,
            },
            indent=2,
        )
    )
