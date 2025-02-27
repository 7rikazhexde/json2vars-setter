import os
from typing import Any, Dict, List, Optional, Tuple

import requests

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import (
    ReleaseInfo,
    check_github_api,
    setup_logging,
)


class NodejsVersionFetcher(BaseVersionFetcher):
    """Fetches Node.js version information from GitHub"""

    def __init__(self) -> None:
        """Initialize with Node.js GitHub repository information"""
        super().__init__("nodejs", "node")

    def _is_stable_tag(self, tag: Dict[str, Any]) -> bool:
        """
        Check if a tag represents a stable Node.js release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        name = tag.get("name", "")

        # Node.js uses format "vX.Y.Z" for stable releases
        return (
            name.startswith("v")
            and len(name.split(".")) == 3
            and not any(
                x in name.lower()
                for x in [
                    "rc",
                    "alpha",
                    "beta",
                    "nightly",
                    "test",
                    "next",
                    "experimental",
                ]
            )
        )

    def _parse_version_from_tag(self, tag: Dict[str, Any]) -> ReleaseInfo:
        """
        Parse version information from a Node.js tag

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

        # Clean version string (e.g., "v14.17.0" -> "14.17.0")
        version = name.lstrip("v")

        # Default is not LTS, this will be updated later if needed
        is_lts = False

        # All filtered tags are considered stable
        prerelease = False

        return ReleaseInfo(
            version=version,
            release_date=None,
            prerelease=prerelease,
            additional_info={
                "tag_name": name,
                "commit": {"sha": tag.get("commit", {}).get("sha")},
                "is_lts": is_lts,
                "tarball_url": tag.get("tarball_url"),
                "zipball_url": tag.get("zipball_url"),
            },
        )

    def _get_additional_info(self) -> Dict[str, Any]:
        """
        Get additional Node.js specific information (LTS status)

        Returns:
            Dictionary with LTS information
        """
        lts_info = self._fetch_nodejs_lts_info()
        return {"lts_info": lts_info}

    def _get_stability_criteria(
        self, releases: List[ReleaseInfo]
    ) -> Tuple[ReleaseInfo, ReleaseInfo]:
        """
        Determine latest and stable versions based on Node.js criteria

        For Node.js, the latest is the most recent release, but stable is the
        most recent LTS (Long Term Support) release if available.

        Args:
            releases: List of release information

        Returns:
            Tuple of (latest_release, stable_release)
        """
        if not releases:
            # 例外を発生させて、リリースが存在しない場合に明示的に処理
            raise ValueError("No releases available")

        # 最新バージョンは常に最初のリリース
        latest = releases[0]

        # 少ないタグセットで動作するようLTS情報を直接検査
        lts_versions = self._fetch_latest_lts_versions()
        self.logger.info(
            f"Found current LTS versions: {', '.join(lts_versions[:3])} (total: {len(lts_versions)})"
        )

        # 現在のタグセットに対してLTSをチェック
        for lts_version in lts_versions:
            # LTSバージョンと一致するリリースを探す
            for release in releases:
                version = release.version
                tag_name = release.additional_info.get("tag_name", "")
                # バージョン番号で比較
                if version == lts_version or tag_name == f"v{lts_version}":
                    self.logger.info(f"Found LTS version in current tags: {version}")
                    return latest, release

        # リリースリストに十分なタグがない可能性があるため、
        # 追加のリリースを取得してLTSを探す
        try:
            # v22.x系の最新リリースを探す
            for lts_version in lts_versions:
                if lts_version.startswith("22."):
                    # 直接APIを呼び出してタグを取得
                    tag = self._get_specific_tag(f"v{lts_version}")
                    if tag:
                        release_info = self._parse_version_from_tag(tag)
                        release_info.additional_info["is_lts"] = True
                        self.logger.info(f"Using LTS version from API: {lts_version}")
                        return latest, release_info
        except Exception as e:
            self.logger.warning(f"Failed to fetch specific LTS tag: {e}")

        # それでも見つからない場合は、現在のリリースセットで偶数メジャーバージョンを探す
        even_major_releases = []
        for release in releases:
            try:
                version_parts = release.version.split(".")
                if len(version_parts) >= 1:
                    major = int(version_parts[0])
                    if major % 2 == 0:  # 偶数メジャーバージョン
                        even_major_releases.append(release)
            except ValueError:
                continue

        if even_major_releases:
            stable = even_major_releases[0]
            self.logger.info(f"Using even major version {stable.version} as stable")
            return latest, stable

        # どれも見つからない場合は最新版を使用するが、警告を出す
        self.logger.warning(
            f"No LTS or even major version found. Using latest {latest.version} as stable. Consider increasing --count."
        )
        return latest, latest

    def _fetch_latest_lts_versions(self) -> List[str]:
        """
        Node.js APIからLTSバージョンを取得し、ソートして返す

        Returns:
            List of LTS version strings without "v" prefix
        """
        try:
            url = "https://nodejs.org/dist/index.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            releases = response.json()

            # LTSバージョンを抽出
            lts_versions = []
            for release in releases:
                version = release.get("version", "").lstrip("v")
                is_lts = release.get("lts", False)
                if is_lts:
                    lts_versions.append(version)

            if lts_versions:
                # バージョンを降順ソート（最新が先頭）
                sorted_versions = sorted(
                    lts_versions,
                    key=lambda v: [int(x) for x in v.split(".")],
                    reverse=True,
                )
                self.logger.info(
                    f"Successfully fetched {len(sorted_versions)} LTS versions from Node.js API"
                )
                return sorted_versions
            else:
                self.logger.warning("No LTS versions found in API response")
                # 空のリストを返す（次のステップで偶数メジャーバージョンを探す）
                return []
        except Exception as e:
            self.logger.warning(f"Failed to fetch LTS versions: {e}")
            return []

    def _get_specific_tag(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """
        特定のタグを直接取得

        Args:
            tag_name: タグ名（例: "v22.14.0"）

        Returns:
            タグ情報またはNone
        """
        try:
            url = f"{self.github_api_base}/repos/{self.github_owner}/{self.github_repo}/git/refs/tags/{tag_name}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            tag_ref = response.json()

            # タグオブジェクトのURLを取得
            tag_url = tag_ref.get("object", {}).get("url")
            if not tag_url:
                return None

            # タグオブジェクトを取得
            tag_response = self.session.get(tag_url, timeout=10)
            tag_response.raise_for_status()
            tag_obj = tag_response.json()

            # コミットURLを取得
            commit_url = tag_obj.get("object", {}).get("url")
            if not commit_url:
                return None

            # コミット情報を取得
            commit_response = self.session.get(commit_url, timeout=10)
            commit_response.raise_for_status()
            commit = commit_response.json()

            # タグ情報を構築
            return {"name": tag_name, "commit": {"sha": commit.get("sha", "")}}
        except Exception as e:
            self.logger.warning(f"Failed to fetch tag {tag_name}: {e}")
            return None

    def _fetch_nodejs_lts_info(self) -> Dict[str, bool]:
        """
        Fetch LTS information from Node.js API

        Returns:
            Dictionary mapping version numbers to LTS status
        """
        try:
            url = "https://nodejs.org/dist/index.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            releases = response.json()

            # Map versions to LTS status
            lts_info: Dict[str, bool] = {}
            for release in releases:
                version = release.get("version", "").lstrip("v")
                is_lts = bool(release.get("lts", False))
                if is_lts:
                    lts_info[version] = is_lts

            self.logger.info(f"Retrieved {len(lts_info)} LTS versions from Node.js API")
            return lts_info
        except Exception as e:
            self.logger.warning(f"Failed to fetch LTS information: {str(e)}")
            return {}


def nodejs_filter_func(tag: Dict[str, Any]) -> bool:
    """Filter function for Node.js tags in API checker"""
    name = tag.get("name", "")
    return (
        name.startswith("v")
        and len(name.split(".")) == 3
        and not any(
            x in name.lower()
            for x in ["rc", "alpha", "beta", "nightly", "test", "next", "experimental"]
        )
    )


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch Node.js version information")
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of versions to fetch (default: 20)",
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
            github_owner="nodejs",
            github_repo="node",
            count=args.count,
            filter_func=nodejs_filter_func,
        )

        # Check LTS information as well
        try:
            print("\nNode.js LTS versions:")
            lts_url = "https://nodejs.org/dist/index.json"
            lts_response = session.get(lts_url, timeout=10)
            lts_response.raise_for_status()
            lts_releases = lts_response.json()

            lts_count = 0
            for release in lts_releases:
                if release.get("lts", False):
                    print(f"- {release.get('version')} (LTS: {release.get('lts')})")
                    lts_count += 1
                    if lts_count >= args.count:
                        break
        except Exception as e:
            print(f"Error fetching LTS info: {str(e)}")

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching Node.js Versions ===")

    # Main processing
    fetcher = NodejsVersionFetcher()
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
