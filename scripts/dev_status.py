"""Script to generate a development status report."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def get_git_stats() -> Dict[str, str]:
    """Get git repository statistics."""
    stats = {}
    
    # Get last commit info
    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
        commit_date = subprocess.check_output(
            ["git", "log", "-1", "--format=%cd"], text=True
        ).strip()
        stats["Last Commit"] = f"{commit_hash} ({commit_date})"
    except subprocess.CalledProcessError:
        stats["Last Commit"] = "Not available"

    # Get branch info
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip()
        stats["Branch"] = branch
    except subprocess.CalledProcessError:
        stats["Branch"] = "Not available"

    return stats


def get_code_stats() -> Dict[str, int]:
    """Get code statistics."""
    stats = {"Python Files": 0, "Total Lines": 0, "Code Lines": 0, "Comment Lines": 0}
    
    for path in Path("src").rglob("*.py"):
        if path.is_file():
            stats["Python Files"] += 1
            with path.open() as f:
                lines = f.readlines()
                stats["Total Lines"] += len(lines)
                for line in lines:
                    line = line.strip()
                    if line:
                        if line.startswith("#"):
                            stats["Comment Lines"] += 1
                        else:
                            stats["Code Lines"] += 1

    return stats


def get_test_coverage() -> Dict[str, str]:
    """Get test coverage information."""
    coverage = {}
    try:
        result = subprocess.run(
            ["pytest", "--cov=src", "--cov-report=term-missing"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        # Extract coverage percentage
        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                parts = line.split()
                if len(parts) >= 4:
                    coverage["Coverage"] = parts[3]
                break
    except Exception:
        coverage["Coverage"] = "Not available"

    return coverage


def main() -> None:
    """Generate and display development status report."""
    print("\n📊 Development Status Report")
    print("=" * 50)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Git Statistics
    print("📝 Git Status")
    print("-" * 30)
    for key, value in get_git_stats().items():
        print(f"{key}: {value}")

    # Code Statistics
    print("\n📈 Code Statistics")
    print("-" * 30)
    for key, value in get_code_stats().items():
        print(f"{key}: {value:,}")

    # Test Coverage
    print("\n🧪 Test Coverage")
    print("-" * 30)
    for key, value in get_test_coverage().items():
        print(f"{key}: {value}")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main() 