import os
import re
from typing import Any, Dict, List, Tuple

import requests

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import (
    ReleaseInfo,
    check_github_api,
    setup_logging,
)


class PythonVersionFetcher(BaseVersionFetcher):
    """Fetches Python version information from GitHub"""

    def __init__(self) -> None:
        """Initialize with Python's GitHub repository information"""
        super().__init__("python", "cpython")

    def _is_stable_tag(self, tag: Dict[str, Any]) -> bool:
        """
        Check if a tag represents a stable Python release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = tag.get("name", "")

        # Python uses format "vX.Y.Z" for stable releases (3.x and 4.x series)
        return name.startswith(("v3", "v4")) and not any(
            x in name.lower()
            for x in [
                "a",
                "rc",
                "b",
                "beta",
                "alpha",
                "pre",
                "preview",
                "dev",
                "test",
                "nightly",
                "snapshot",
            ]
        )

    def _parse_version_from_tag(self, tag: Dict[str, Any]) -> ReleaseInfo:
        """
        Parse version information from a Python tag

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

        # Clean version string (e.g., "v3.12.0" -> "3.12.0")
        version = name.lstrip("v")

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

    def _get_stability_criteria(
        self, releases: List[ReleaseInfo]
    ) -> Tuple[ReleaseInfo, ReleaseInfo]:
        """
        Python の安定版と最新版の判定

        Python では:
        - latest: 最新のリリースバージョン
        - stable: 通常は現在の広く採用されているバージョン（1つ前のマイナーバージョン）
          または明示的に「stable」とマークされたバージョン

        Args:
            releases: リリース情報のリスト

        Returns:
            (latest_release, stable_release) のタプル
        """
        if not releases:
            # 例外を発生させて、リリースが存在しない場合に明示的に処理
            raise ValueError("No releases available")

        # 最新バージョンは常に最初のリリース
        latest = releases[0]

        # バージョン番号を取得して解析
        latest_version = latest.version
        match = re.match(r"(\d+)\.(\d+)\.(\d+)", latest_version)

        if match:
            major, minor, patch = map(int, match.groups())
            # 現在のマイナーバージョンから1つ前を探す
            prev_minor = minor - 1

            # 1つ前のマイナーバージョンを持つリリースを検索
            for release in releases:
                r_match = re.match(r"(\d+)\.(\d+)\.(\d+)", release.version)
                if r_match:
                    r_major, r_minor, r_patch = map(int, r_match.groups())
                    if r_major == major and r_minor == prev_minor:
                        self.logger.info(
                            f"Using {release.version} as stable vs latest {latest_version}"
                        )
                        return latest, release

        # 適切な安定版が見つからない場合は最新を使用
        self.logger.info(
            f"No suitable stable version found, using latest {latest_version} as stable"
        )
        return latest, latest


def python_filter_func(tag: Dict[str, Any]) -> bool:
    """Filter function for Python tags in API checker"""
    name = tag.get("name", "")

    # 不安定版を示すキーワードを完全に検出するための正規表現パターン
    unstable_pattern = r"(a|rc|b|beta|alpha|pre|preview|dev|test|nightly|snapshot)"

    # タグが v3 または v4 で始まり、不安定版キーワードを含まないこと
    return (
        name.startswith(("v3", "v4"))
        and
        # 正規表現を使用して、キーワードが完全に一致するかをチェック
        not re.search(rf"\d+\.{unstable_pattern}", name.lower())
        and not re.search(rf"{unstable_pattern}", name.lower())
    )


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch Python version information")
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
            github_owner="python",
            github_repo="cpython",
            count=args.count,
            filter_func=python_filter_func,
        )

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching Python Versions ===")

    # Main processing
    fetcher = PythonVersionFetcher()
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
