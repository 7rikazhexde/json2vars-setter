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


def version_sort_key(release: Dict[str, Any]) -> tuple:
    """バージョン番号に基づいてソートするためのキー関数"""
    version = release["version"].lstrip("v")
    # メジャー.マイナー.パッチ形式のバージョンを数値のタプルに変換
    try:
        return tuple(map(int, version.split(".")))
    except ValueError:
        return (0, 0, 0)  # 解析できない場合は最小値を返す


def fetch_nodejs_versions() -> VersionInfo:
    """Fetch Node.js versions."""
    try:
        session = requests.Session()
        url = "https://nodejs.org/dist/index.json"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        releases = response.json()

        result = VersionInfo(
            details={"source": url, "fetch_time": response.headers.get("date")}
        )

        if releases:
            # バージョン番号でソート（降順）
            releases.sort(key=version_sort_key, reverse=True)

            # Get latest version (including non-LTS)
            latest_release = releases[0]
            result.latest = latest_release["version"].lstrip("v")
            result.details["latest_info"] = {
                "version": result.latest,
                "date": latest_release.get("date"),
                "is_lts": latest_release.get("lts", False),
                "npm": latest_release.get("npm"),
                "v8": latest_release.get("v8"),
            }

            # Get latest LTS version
            lts_releases = [r for r in releases if r.get("lts", False)]
            if lts_releases:
                # LTSの中で最新のものを取得
                lts_releases.sort(key=version_sort_key, reverse=True)
                stable_release = lts_releases[0]
                result.stable = stable_release["version"].lstrip("v")
                result.details["stable_info"] = {
                    "version": result.stable,
                    "date": stable_release.get("date"),
                    "lts": stable_release.get("lts"),
                    "npm": stable_release.get("npm"),
                    "v8": stable_release.get("v8"),
                }

            # Add recent versions for reference
            result.details["recent_versions"] = {
                "all": [r["version"].lstrip("v") for r in releases[:5]],
                "lts": [r["version"].lstrip("v") for r in lts_releases[:5]],
            }

        return result

    except Exception as e:
        error_msg = str(e)
        return VersionInfo(details={"error": error_msg, "error_type": type(e).__name__})


if __name__ == "__main__":
    versions = fetch_nodejs_versions()
    print("\n=== Node.js Versions ===")
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
