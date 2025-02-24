import json
import re
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


def extract_versions_from_section(content: str, section: str) -> List[str]:
    """Extract versions from a YAML section."""
    versions: List[str] = []

    # セクションの開始位置を見つける
    section_start = content.find(f"{section}:")
    if section_start == -1:
        return versions

    # 次のセクションの開始位置を見つける
    next_section_match = re.search(
        r"\n\w+:", content[section_start + len(section) + 1 :]
    )
    section_end = (
        next_section_match.start() + section_start + len(section) + 1
        if next_section_match
        else len(content)
    )

    # セクション内容を抽出
    section_content = content[section_start:section_end]

    # バージョン番号を抽出（空行を除く）
    if re.search(
        r":\s*\n\s+- \d+", section_content
    ):  # バージョン番号が実際に存在するか確認
        versions = re.findall(r"- (\d+\.\d+\.\d+)", section_content)

    return versions


def fetch_ruby_versions() -> VersionInfo:
    """Fetch Ruby versions."""
    try:
        session = requests.Session()
        url = "https://raw.githubusercontent.com/ruby/www.ruby-lang.org/master/_data/downloads.yml"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        content = response.text

        result = VersionInfo(
            details={
                "source": url,
                "fetch_time": response.headers.get("date"),
                "content_preview": "\n".join(content.split("\n")[:15]),
            }
        )

        # Get all versions from different sections
        preview_versions = extract_versions_from_section(content, "preview")
        stable_versions = extract_versions_from_section(content, "stable")
        security_versions = extract_versions_from_section(
            content, "security_maintenance"
        )
        eol_versions = extract_versions_from_section(content, "eol")

        # Store all versions in details
        result.details.update(
            {
                "preview_versions": preview_versions,
                "stable_versions": stable_versions,
                "security_maintenance_versions": security_versions,
                "eol_versions": eol_versions,
            }
        )

        # Set latest and stable versions
        if preview_versions:
            result.latest = preview_versions[0]
            result.details["latest_info"] = {
                "version": result.latest,
                "type": "preview",
            }

        if stable_versions:
            result.stable = stable_versions[0]
            result.details["stable_info"] = {
                "version": result.stable,
                "type": "stable",
                "all_stable": stable_versions,
            }
            # If no preview version, use first stable as latest
            if not result.latest:
                result.latest = result.stable
                result.details["latest_info"] = {
                    "version": result.latest,
                    "type": "stable",
                }

        return result

    except Exception as e:
        error_msg = str(e)
        return VersionInfo(details={"error": error_msg, "error_type": type(e).__name__})


if __name__ == "__main__":
    versions = fetch_ruby_versions()
    print("\n=== Ruby Versions ===")
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
