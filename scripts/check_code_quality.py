"""Script to run all code quality checks in sequence."""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(command: List[str]) -> Tuple[int, str]:
    """Run a command and return its exit code and output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return 1, str(e)


def main() -> int:
    """Run all code quality checks and return overall status."""
    checks = [
        (["black", "--check", "."], "Code formatting (black)"),
        (["isort", "--check", "."], "Import sorting (isort)"),
        (["flake8", "."], "Code linting (flake8)"),
        (["mypy", "."], "Type checking (mypy)"),
        (["pytest", "--cov=src", "--cov-report=term-missing"], "Tests (pytest)"),
    ]

    failed_checks = []
    for command, name in checks:
        print(f"\nRunning {name}...")
        exit_code, output = run_command(command)
        print(output)
        
        if exit_code != 0:
            failed_checks.append(name)
            print(f"❌ {name} failed!")
        else:
            print(f"✅ {name} passed!")

    if failed_checks:
        print("\n❌ The following checks failed:")
        for check in failed_checks:
            print(f"  - {check}")
        return 1
    
    print("\n✅ All checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 