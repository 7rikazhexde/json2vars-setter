import json
import re
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


def fetch_rust_versions() -> VersionInfo:
    """Fetch Rust versions."""
    try:
        # まずGitHubのリリースAPIを試す（将来的にlatestとstableが分かれる可能性に備える）
        github_url = "https://api.github.com/repos/rust-lang/rust/releases"
        session = requests.Session()
        try:
            github_response = session.get(github_url, timeout=10)
            github_response.raise_for_status()
            releases = github_response.json()

            if releases:
                result = VersionInfo()
                # GitHubのリリースから取得
                result.latest = releases[0]["tag_name"].lstrip("v")
                stable_release = next(
                    (r for r in releases if not r.get("prerelease", False)), None
                )
                result.stable = (
                    stable_release["tag_name"].lstrip("v")
                    if stable_release
                    else result.latest
                )
                result.details["source"] = "github_api"
                result.details["release_date"] = (
                    releases[0].get("published_at", "").split("T")[0]
                )
                result.details["recent_versions"] = [
                    r["tag_name"].lstrip("v") for r in releases[:5]
                ]
                return result
        except Exception:
            # GitHubのAPIが失敗した場合は、従来のRELEASES.mdを使用
            pass

        # 従来のRELEASES.mdからの取得（フォールバック）
        url = "https://raw.githubusercontent.com/rust-lang/rust/master/RELEASES.md"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        content = response.text

        result = VersionInfo()
        result.details["source"] = "releases_md"

        # バージョン番号を抽出
        version_pattern = r"Version\s+(\d+\.\d+\.\d+)"
        versions = re.findall(version_pattern, content)

        if versions:
            # バージョンを数値でソート（最新順）
            versions.sort(key=lambda v: [int(n) for n in v.split(".")], reverse=True)

            # 現時点では最新 = 安定版
            result.latest = versions[0]
            result.stable = versions[0]

            # リリース日を取得
            date_pattern = f"Version {versions[0]} \\((.*?)\\)"
            date_match = re.search(date_pattern, content)
            if date_match:
                result.details["release_date"] = date_match.group(1)

            # 最近のバージョン
            result.details["recent_versions"] = versions[:5]

        return result

    except Exception as e:
        error_msg = str(e)
        return VersionInfo(details={"error": error_msg})


if __name__ == "__main__":
    versions = fetch_rust_versions()
    print("\n=== Rust Versions ===")
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
