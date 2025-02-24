import argparse
import json
import os
from typing import Any, Dict, List, Optional

from json2vars_setter.version.version_fetcher import VersionType, fetch_all_versions


def generate_matrix_json(
    output_dir: Optional[str] = None, specific_lang: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate matrix JSON with stable versions for specified languages.

    :param output_dir: Directory to save the JSON files
    :param specific_lang: Optional specific language to generate JSON for
    :return: Dictionary of generated JSONs
    """
    # Fetch stable versions
    version_data = fetch_all_versions(VersionType.STABLE)

    # Create output directory if not exists
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Base matrix structure from the original matrix.json
    base_matrix: Dict[str, Any] = {
        "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
        "versions": {},
        "ghpages_branch": "ghpages",
    }

    # Determine which languages to process
    languages_to_process: List[str] = (
        [specific_lang] if specific_lang else list(version_data["versions"].keys())
    )

    # Generated JSONs
    generated_jsons: Dict[str, Any] = {}

    for lang in languages_to_process:
        if lang not in version_data["versions"]:
            print(f"Warning: No stable version found for {lang}")
            continue

        # Create a copy of the base matrix
        matrix = base_matrix.copy()
        matrix["versions"] = {}  # Reset versions dict to avoid mutation of base_matrix

        # Add stable version for the specified language
        matrix["versions"][lang] = (
            [version_data["versions"][lang]]
            if isinstance(version_data["versions"][lang], str)
            else version_data["versions"][lang]
        )

        # Filename logic
        if specific_lang:
            filename = f"matrix-{lang}-stable.json"
        else:
            filename = "matrix-stable.json"

        # Full path for saving
        if output_dir:
            filepath = os.path.join(output_dir, filename)
        else:
            filepath = filename

        # Save JSON
        with open(filepath, "w") as f:
            json.dump(matrix, f, indent=4)

        print(f"Generated {filepath}")
        generated_jsons[lang] = matrix

    return generated_jsons


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate GitHub Actions Matrix JSON with Stable Versions"
    )
    parser.add_argument(
        "--lang",
        type=str,
        help="Specific language to generate JSON for (e.g., 'python')",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".github/workflows",
        help="Output directory for JSON files (default: .github/workflows)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    result = generate_matrix_json(output_dir=args.output_dir, specific_lang=args.lang)

    if args.debug:
        print("\nGenerated Matrix JSON:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
