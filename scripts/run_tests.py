import argparse
import subprocess
import sys


def run_command(command: list[str]) -> str:
    """Run a command, stream its output live, and return the captured text."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    output: str = ""
    if process.stdout:
        for line in process.stdout:
            print(line, end="")
            output += line
    process.wait()
    return output


def get_test_command(report_type: str) -> list[str]:
    base_command = ["pytest", "--durations=0", "--junitxml=pytest.xml"]

    if report_type == "xml":
        cov_report = "--cov-report=xml:coverage.xml"
    elif report_type == "term":
        cov_report = "--cov-report=term-missing"
    else:
        raise ValueError(f"Unsupported report type: {report_type}")

    return [*base_command, cov_report, "--cov=json2vars_setter", "tests/"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run pytest with specific coverage report type."
    )
    parser.add_argument(
        "--report",
        choices=["xml", "term"],
        default="term",
        help='Specify the coverage report type: "xml" for XML report, "term" for terminal report',
    )
    args = parser.parse_args()

    # Run pytest once, streaming to the console while capturing the output so it
    # can be written to pytest-coverage.txt in a single pass (no shell-specific
    # tee/Tee-Object branching, no redundant re-write).
    command = get_test_command(args.report)
    output = run_command([sys.executable, "-m", *command])

    with open("pytest-coverage.txt", "w", encoding="utf-8") as f:
        f.write(output)


if __name__ == "__main__":
    main()
