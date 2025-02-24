import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Union

from json2vars_setter.version.go_fetch import fetch_go_versions
from json2vars_setter.version.nodejs_fetch import fetch_nodejs_versions
from json2vars_setter.version.python_fetch import fetch_python_versions
from json2vars_setter.version.ruby_fetch import fetch_ruby_versions
from json2vars_setter.version.rust_fetch import fetch_rust_versions


class VersionType(Enum):
    LATEST = "latest"
    STABLE = "stable"
    BOTH = "both"


@dataclass
class LanguageVersions:
    python: Dict[str, Any]
    ruby: Dict[str, Any]
    nodejs: Dict[str, Any]
    go: Dict[str, Any]
    rust: Dict[str, Any]


def get_version_output(
    version_info: Dict[str, Any], version_type: VersionType
) -> Union[str, List[str], None]:
    """指定されたバージョンタイプに応じて出力を生成"""
    if not version_info:
        return None

    latest = version_info.get("latest")
    stable = version_info.get("stable")

    if version_type == VersionType.LATEST:
        return latest
    elif version_type == VersionType.STABLE:
        return stable
    else:  # BOTH
        versions = []
        if latest:
            versions.append(latest)
        if stable and stable != latest:
            versions.append(stable)
        return versions if versions else None


def fetch_all_versions(
    version_type: VersionType = VersionType.STABLE,
) -> Dict[str, Any]:
    """全ての言語のバージョン情報を取得"""
    try:
        # 各言語のバージョン情報を取得
        python_info = fetch_python_versions()
        ruby_info = fetch_ruby_versions()
        nodejs_info = fetch_nodejs_versions()
        go_info = fetch_go_versions()
        rust_info = fetch_rust_versions()

        # バージョンタイプに応じた出力を生成
        versions = {
            "python": get_version_output(vars(python_info), version_type),
            "ruby": get_version_output(vars(ruby_info), version_type),
            "nodejs": get_version_output(vars(nodejs_info), version_type),
            "go": get_version_output(vars(go_info), version_type),
            "rust": get_version_output(vars(rust_info), version_type),
        }

        # 詳細情報を追加
        details = {
            "python": python_info.details if hasattr(python_info, "details") else None,
            "ruby": ruby_info.details if hasattr(ruby_info, "details") else None,
            "nodejs": nodejs_info.details if hasattr(nodejs_info, "details") else None,
            "go": go_info.details if hasattr(go_info, "details") else None,
            "rust": rust_info.details if hasattr(rust_info, "details") else None,
        }

        return {
            "versions": {k: v for k, v in versions.items() if v is not None},
            "details": {k: v for k, v in details.items() if v is not None},
        }

    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch programming language versions")
    parser.add_argument(
        "--type",
        choices=["latest", "stable", "both"],
        default="stable",
        help="Type of version to fetch (default: stable)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Show detailed information"
    )

    args = parser.parse_args()
    version_type = VersionType(args.type)

    result = fetch_all_versions(version_type)

    print("\n=== Programming Language Versions ===")
    if args.debug:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result["versions"], indent=2))
