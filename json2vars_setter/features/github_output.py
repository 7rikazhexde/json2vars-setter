import json
import os
import sys
from typing import Dict, List, Optional


def set_github_output(outputs: Dict[str, str], debug: bool) -> None:
    """
    Set multiple GitHub Actions output variables by appending them to the GITHUB_OUTPUT file at once.

    Args:
        outputs: Dictionary of output variables to set.
        debug: If True, print debug information to standard output.

    Returns:
        None
    """
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output is None:
        print("GITHUB_OUTPUT is not set. Unable to set output.")
        sys.exit(1)

    # Write all outputs to GITHUB_OUTPUT at once
    with open(github_output, "a") as fh:
        for name, value in outputs.items():
            fh.write(f"{name}={value}\n")
        fh.flush()

    if debug:
        print(f"Debug: Written to GITHUB_OUTPUT -> {outputs}")


def parse_json(data: object, prefix: str = "", debug: bool = False) -> Dict[str, str]:
    """
    Recursively parse JSON data and collect GitHub Actions outputs.

    Args:
        data: The JSON data to be parsed.
        prefix: Prefix to add to the variable names (used for nested dictionaries).
        debug: If True, print debug information to standard output.

    Returns:
        A dictionary of parsed output variables.
    """
    outputs = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                if debug:
                    print(f"Debug: Parsing nested value for key '{key}'")
                outputs.update(parse_json(value, prefix + key.upper() + "_", debug))
            else:
                outputs[f"{prefix}{key.upper()}"] = str(value)
                if debug:
                    print(f"Debug: Parsed key='{prefix}{key.upper()}' value='{value}'")
    elif isinstance(data, list):
        list_values = json.dumps(data)
        outputs[prefix[:-1]] = list_values  # Remove trailing underscore
        if debug:
            print(f"Debug: Parsed list '{prefix[:-1]}' value='{list_values}'")
        for index, item in enumerate(data):
            if isinstance(item, dict):
                outputs.update(parse_json(item, prefix + f"{index}_", debug))
            else:
                outputs[f"{prefix}{index}"] = str(item)
                if debug:
                    print(f"Debug: Parsed list item '{prefix}{index}' value='{item}'")
    else:
        raise TypeError("Unsupported data type encountered. Expected dict or list.")

    return outputs


def build_matrix_outputs(data: object) -> Dict[str, str]:
    """Build ready-to-use per-language matrix objects from the parsed JSON.

    For every language under ``versions``, emit a ``matrix_<lang>`` output whose value
    is a JSON object ``{"os": [...], "version": [...]}`` (``os`` omitted if the JSON has
    none). A consumer can then assign a whole matrix with a single ``fromJson`` and read
    ``${{ matrix.version }}`` / ``${{ matrix.os }}`` directly — no per-axis ``fromJson``
    and no index access. The original ``os`` / ``versions_<lang>`` outputs are unaffected,
    so this is purely additive.

    Args:
        data: The original JSON data (before flattening).

    Returns:
        A dictionary of ``MATRIX_<LANG>`` outputs (empty if the JSON has no ``versions``).
    """
    outputs: Dict[str, str] = {}
    if not isinstance(data, dict):
        return outputs

    versions = data.get("versions")
    if not isinstance(versions, dict):
        return outputs

    os_list = data.get("os")
    for language, version_list in versions.items():
        matrix: Dict[str, object] = {}
        if os_list is not None:
            matrix["os"] = os_list
        matrix["version"] = version_list
        outputs[f"MATRIX_{language.upper()}"] = json.dumps(matrix)

    return outputs


def print_output_summary(data: object) -> None:
    """Print a concise, matrix-proportional summary of the parsed outputs.

    Only the keys actually present in the JSON are shown. For a matrix that lists
    Python and Node.js, just those (plus ``os`` / ``ghpages_branch``) are printed,
    rather than every supported language — so the log stays proportional to the
    matrix as the set of supported languages grows.

    Args:
        data: The original JSON data (before flattening).
    """
    if not isinstance(data, dict):
        return

    print("Outputs summary:")
    for key, value in data.items():
        if key == "versions" and isinstance(value, dict):
            for language, versions in value.items():
                print(f"  {language} versions: {json.dumps(versions)}")
        elif isinstance(value, (list, dict)):
            print(f"  {key}: {json.dumps(value)}")
        else:
            print(f"  {key}: {value}")


def main(argv: Optional[List[str]] = None) -> None:
    """Read a JSON file and write its contents to GITHUB_OUTPUT.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``). The first element is
            the JSON file path; ``--debug`` enables debug output.
    """
    args = sys.argv[1:] if argv is None else argv

    # Retrieve the JSON file path and optional debug flag from command line arguments
    json_file = args[0]
    debug = "--debug" in args

    # Load the JSON data from the file
    with open(json_file, "r") as f:
        data = json.load(f)

    # Parse the JSON data and write to GITHUB_OUTPUT
    collected_outputs = parse_json(data, debug=debug)
    # Add the convenience per-language matrix objects so consumers can assign a whole
    # matrix with a single fromJson and use ${{ matrix.version }} / ${{ matrix.os }}.
    collected_outputs.update(build_matrix_outputs(data))
    set_github_output(collected_outputs, debug=debug)

    # Print a concise summary that scales with the matrix (only the keys present
    # in the JSON), replacing the former static per-language debug echo block.
    print_output_summary(data)


if __name__ == "__main__":
    main()
