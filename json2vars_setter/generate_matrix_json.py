import argparse
import json
import os
from typing import Any, Dict, List, Optional

from json2vars_setter.version.version_fetcher import VersionType, fetch_all_versions


def generate_matrix_json(
    *,
    input_file: Optional[str] = None,
    output_dir: Optional[str] = None,
    specific_lang: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Generate or update matrix JSON with stable versions.

    :param input_file: Path to input JSON file for updating existing matrix
    :param output_dir: Directory to save the generated JSON files
    :param specific_lang: Optional specific language to generate JSON for
    :param debug: Enable debug output
    :return: Dictionary of generated/updated matrix JSON
    """
    # Fetch stable versions
    version_data = fetch_all_versions(VersionType.STABLE)

    # Base matrix structure
    base_matrix: Dict[str, Any] = {
        "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
        "versions": {},
        "ghpages_branch": "ghpages",
    }

    # If input file is specified, load and update existing matrix
    if input_file:
        try:
            with open(input_file, "r") as f:
                base_matrix.update(json.load(f))
        except FileNotFoundError:
            # Use default base_matrix if file doesn't exist
            os.makedirs(os.path.dirname(input_file), exist_ok=True)

    # Determine which languages to process
    languages_to_process: List[str] = (
        [specific_lang]
        if specific_lang
        else (
            list(base_matrix.get("versions", {}).keys())
            if input_file
            else list(version_data["versions"].keys())
        )
    )

    # Generated/Updated JSONs
    result_jsons: Dict[str, Any] = {}

    for lang in languages_to_process:
        if lang not in version_data.get("versions", {}):
            print(f"Warning: No stable version found for {lang}")
            continue

        # Create a copy of the base matrix for each language
        matrix = base_matrix.copy()
        matrix["versions"] = {}  # Reset versions dict to avoid mutation

        # Add stable version for the language
        matrix["versions"][lang] = (
            [version_data["versions"][lang]]
            if isinstance(version_data["versions"][lang], str)
            else version_data["versions"][lang]
        )

        # Handle file saving
        if output_dir:
            # Create output directory if not exists
            os.makedirs(output_dir, exist_ok=True)

            # Generate filename based on mode
            filename = (
                f"{lang}_project_matrix.json" if specific_lang else "matrix-stable.json"
            )
            filepath = os.path.join(output_dir, filename)

            # Save JSON
            with open(filepath, "w") as f:
                json.dump(matrix, f, indent=4)
            print(f"Generated {filepath}")

        # Save to input file if specified
        if input_file:
            with open(input_file, "w") as f:
                json.dump(matrix, f, indent=4)
            print(f"Updated matrix JSON: {input_file}")

        result_jsons[lang] = matrix

    # Debug output
    if debug:
        print("\nGenerated/Updated Matrix JSON:")
        print(json.dumps(result_jsons, indent=2))

    return result_jsons


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate or Update GitHub Actions Matrix JSON with Stable Versions"
    )
    parser.add_argument(
        "--input-file",
        help="Path to input JSON file for updating (optional)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for generated JSON files (optional)",
    )
    parser.add_argument(
        "--lang",
        type=str,
        help="Specific language to generate JSON for (e.g., 'python')",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    if not (args.input_file or args.output_dir):
        # デフォルトの出力ディレクトリを設定
        args.output_dir = ".github/workflows"

    generate_matrix_json(
        input_file=args.input_file,
        output_dir=args.output_dir,
        specific_lang=args.lang,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
