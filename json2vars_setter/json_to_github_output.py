import json
import os
import sys
from typing import Any, Dict


def set_github_output(outputs: Dict[str, str], debug: bool) -> None:
    """
    Set multiple GitHub Actions output variables by appending them to the GITHUB_OUTPUT file at once.

    :param outputs: Dictionary of output variables to set.
    :param debug: If True, print debug information to standard output.
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


def parse_json(data: Any, prefix: str = "", debug: bool = False) -> Dict[str, str]:
    """
    Recursively parse JSON data and collect GitHub Actions outputs.

    :param data: The JSON data to be parsed.
    :param prefix: Prefix to add to the variable names (used for nested dictionaries).
    :param debug: If True, print debug information to standard output.
    :return: A dictionary of parsed output variables.
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

    return outputs


if __name__ == "__main__":
    # Retrieve the JSON file path and optional debug flag from command line arguments
    json_file: str = sys.argv[1]
    debug = "--debug" in sys.argv

    # Load the JSON data from the file
    with open(json_file, "r") as f:
        data = json.load(f)

    # Parse the JSON data and write to GITHUB_OUTPUT
    collected_outputs = parse_json(data, debug=debug)
    set_github_output(collected_outputs, debug=debug)
