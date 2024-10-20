import argparse
import platform
import subprocess


def run_command(command: str) -> str:
    process = subprocess.Popen(
        command,
        shell=True,
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
    return output


def get_test_command(report_type: str) -> str:
    base_command: str = "pytest --durations=0 --junitxml=pytest.xml"

    if report_type == "xml":
        cov_report = '--cov-report "xml:coverage.xml"'
    elif report_type == "term":
        cov_report = "--cov-report=term-missing"
    else:
        raise ValueError(f"Unsupported report type: {report_type}")

    full_command = f"{base_command} {cov_report} --cov=project_a tests/"

    if platform.system() == "Windows":
        print(f"system/OS is {platform.system()}")
        return f'powershell -Command "{full_command} | Tee-Object -FilePath pytest-coverage.txt"'
    else:
        print(f"system/OS is {platform.system()}")
        return f"{full_command} | tee pytest-coverage.txt"


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

    command: str = get_test_command(args.report)
    output: str = run_command(command)

    with open("pytest-coverage.txt", "w", encoding="utf-8") as f:
        f.write(output)


if __name__ == "__main__":
    main()
