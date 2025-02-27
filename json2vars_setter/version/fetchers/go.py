import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import ReleaseInfo, setup_logging


class GoVersionFetcher(BaseVersionFetcher):
    """Fetches Go version information from GitHub"""

    def __init__(self) -> None:
        """Initialize with Go's GitHub repository information"""
        super().__init__("golang", "go")

    def _is_stable_tag(self, tag: Dict[str, Any]) -> bool:
        """
        Check if a tag represents a stable Go release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = tag.get("name", "")

        # Go uses format "goX.Y.Z" for stable releases
        return (
            name.startswith("go")
            and len(name.replace("go", "").split(".")) == 3
            and not any(
                x in name.lower()
                for x in [
                    "rc",
                    "alpha",
                    "beta",
                    "preview",
                    "pre",
                    "test",
                    "dev",
                    "snapshot",
                ]
            )
        )

    def _parse_version_from_tag(self, tag: Dict[str, Any]) -> ReleaseInfo:
        """
        Parse version information from a Go tag

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

        # Clean version string (e.g., "go1.22.1" -> "1.22.1")
        version = name.lstrip("go")

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
        Go の安定版と最新版の判定

        Go では:
        - latest: 最新のリリースバージョン
        - stable: 通常は最新の前のマイナーバージョン、または
          リリースから十分に時間が経過した安定したバージョン

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


# 直接APIをチェックする独自関数
def check_api(
    session: requests.Session, count: Optional[int] = None, verbose: bool = False
) -> None:
    """
    GitHubから直接タグを確認する（複数ページのサポート付き）

    Args:
        session: Requests session to use
        count: Optional number of tags to display
        verbose: Whether to print the check output
    """
    if not verbose:
        return

    count = count or 5  # デフォルト値の設定
    stable_tags: List[Dict[str, Any]] = []
    page = 1
    max_pages = 3  # 最大3ページまで確認

    url = "https://api.github.com/repos/golang/go/tags"
    print("\n=== Checking GitHub API ===")
    print("Checking golang/go tags...")

    while len(stable_tags) < count and page <= max_pages:
        try:
            params = {"page": page, "per_page": 100}
            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()
            tags = response.json()

            if page == 1:  # 最初のページの情報のみ表示
                print("Status Code: {}".format(response.status_code))
                print(f"Checking page {page}...")

                if verbose > 1 and tags:
                    print("\nFirst 5 raw tags on page 1:")
                    for tag in tags[:5]:
                        print(f"- {tag.get('name')}")

            if not tags:
                break

            # 安定版のみをフィルタリング
            new_stable_tags = []
            for tag in tags:
                name = tag.get("name", "")
                if (
                    name.startswith("go")
                    and len(name.replace("go", "").split(".")) == 3
                    and not any(
                        x in name.lower()
                        for x in [
                            "rc",
                            "alpha",
                            "beta",
                            "preview",
                            "pre",
                            "test",
                            "dev",
                            "snapshot",
                        ]
                    )
                ):
                    new_stable_tags.append(tag)

            print(f"Found {len(new_stable_tags)} stable tags on page {page}")
            stable_tags.extend(new_stable_tags)

            if len(tags) < 100:  # 最後のページ
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
    parser = argparse.ArgumentParser(description="Fetch Go version information")
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
        print("\n=== Fetching Go Versions ===")

    # Main processing
    fetcher = GoVersionFetcher()
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
