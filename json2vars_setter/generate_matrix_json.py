import argparse
import json
import os
from typing import Any, Dict, Optional

from json2vars_setter.version.version_fetcher import VersionType, fetch_all_versions


def update_matrix_json(
    input_file: Optional[str] = None, debug: bool = False
) -> Dict[str, Any]:
    """
    Update matrix JSON with stable versions.

    :param input_file: Path to input JSON file (optional)
    :param debug: Enable debug output
    :return: Updated matrix JSON
    """
    # Default to matrix.json if no input file specified
    if not input_file:
        input_file = ".github/workflows/matrix.json"

        # Ensure the directory exists
        os.makedirs(os.path.dirname(input_file), exist_ok=True)

    # Initialize matrix data structure
    matrix_data: Dict[str, Any] = {
        "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
        "versions": {},
        "ghpages_branch": "ghpages",
    }

    # Load existing matrix JSON if file exists
    try:
        with open(input_file, "r") as f:
            matrix_data.update(json.load(f))
    except FileNotFoundError:
        # Use default matrix_data if file doesn't exist
        pass

    # Fetch stable versions
    version_data = fetch_all_versions(VersionType.STABLE)

    # Update versions for each language in the existing matrix
    for lang in matrix_data.get("versions", {}).keys():
        if lang in version_data.get("versions", {}):
            matrix_data["versions"][lang] = (
                [version_data["versions"][lang]]
                if isinstance(version_data["versions"][lang], str)
                else version_data["versions"][lang]
            )

    # Debug output
    if debug:
        print("\nUpdated Matrix JSON:")
        print(json.dumps(matrix_data, indent=2))

    # Save the updated JSON
    with open(input_file, "w") as f:
        json.dump(matrix_data, f, indent=4)

    print(f"Updated matrix JSON: {input_file}")

    return matrix_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update Matrix JSON with Stable Versions"
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Path to input JSON file (optional, defaults to .github/workflows/matrix.json)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    # If input file is provided as a positional argument, use it
    update_matrix_json(input_file=args.input_file, debug=args.debug)


if __name__ == "__main__":
    main()
