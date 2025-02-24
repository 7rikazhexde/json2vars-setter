import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests


@dataclass
class VersionInfo:
    latest: Optional[str] = None
    stable: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.details is None:
            self.details = {}


def version_sort_key(release: Dict[str, Any]) -> tuple:
    """バージョン番号に基づいてソートするためのキー関数"""
    version = release["version"].lstrip("go")
    try:
        return tuple(map(int, version.split(".")))
    except ValueError:
        return (0, 0, 0)


def fetch_go_versions() -> VersionInfo:
    """Fetch Go versions."""
    try:
        session = requests.Session()
        url = "https://go.dev/dl/?mode=json"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        releases = response.json()

        result = VersionInfo(
            details={"source": url, "fetch_time": response.headers.get("date")}
        )

        if releases:
            # バージョン番号でソート（降順）
            releases.sort(key=version_sort_key, reverse=True)

            # Get latest version (newest stable version)
            latest_release = releases[0]
            result.latest = latest_release["version"].lstrip("go")
            result.details["latest_info"] = {
                "version": result.latest,
                "stable": latest_release.get("stable", True),
                "kind": latest_release.get("kind", ""),
                "files_count": len(latest_release.get("files", [])),
                "files_sample": [
                    f.get("filename") for f in latest_release.get("files", [])[:3]
                ],
                "available_platforms": list(
                    set(
                        f.get("os", "")
                        for f in latest_release.get("files", [])
                        if f.get("os")
                    )
                ),
            }

            # Get stable version (previous stable version)
            if len(releases) > 1:
                stable_release = releases[1]  # 1つ前のリリースを stable とする
                result.stable = stable_release["version"].lstrip("go")
                result.details["stable_info"] = {
                    "version": result.stable,
                    "stable": True,
                    "kind": stable_release.get("kind", ""),
                    "files_count": len(stable_release.get("files", [])),
                    "files_sample": [
                        f.get("filename") for f in stable_release.get("files", [])[:3]
                    ],
                    "available_platforms": list(
                        set(
                            f.get("os", "")
                            for f in stable_release.get("files", [])
                            if f.get("os")
                        )
                    ),
                }

            # Add version history
            result.details["versions"] = {
                "total_count": len(releases),
                "recent": {"all": [r["version"].lstrip("go") for r in releases[:5]]},
            }

            # Add minor version tracking
            versions_by_minor: Dict[str, List[str]] = {}
            for release in releases:
                version = release["version"].lstrip("go")
                minor = ".".join(version.split(".")[:2])  # 1.24 など
                if minor not in versions_by_minor:
                    versions_by_minor[minor] = []
                versions_by_minor[minor].append(version)

            result.details["version_branches"] = {
                minor: versions[:3]  # 各マイナーバージョンの最新3つ
                for minor, versions in versions_by_minor.items()
            }

        return result

    except Exception as e:
        error_msg = str(e)
        return VersionInfo(details={"error": error_msg, "error_type": type(e).__name__})


if __name__ == "__main__":
    versions = fetch_go_versions()
    print("\n=== Go Versions ===")
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
