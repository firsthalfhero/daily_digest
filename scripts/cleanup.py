"""Script to clean up Python cache files and temporary files."""

import shutil
from pathlib import Path
from typing import List, Set


def find_cache_dirs(root: Path) -> Set[Path]:
    """Find all Python cache directories."""
    cache_dirs = set()
    for path in root.rglob("**/*"):
        if path.is_dir() and path.name in {"__pycache__", ".pytest_cache", ".coverage", ".mypy_cache"}:
            cache_dirs.add(path)
    return cache_dirs


def find_temp_files(root: Path) -> Set[Path]:
    """Find temporary files created during development."""
    temp_files = set()
    for path in root.rglob("**/*"):
        if path.is_file() and any(
            path.name.endswith(ext) for ext in {".pyc", ".pyo", ".pyd", ".so", ".coverage"}
        ):
            temp_files.add(path)
    return temp_files


def main() -> None:
    """Clean up cache directories and temporary files."""
    root = Path(".")
    
    # Find and remove cache directories
    cache_dirs = find_cache_dirs(root)
    if cache_dirs:
        print("\nRemoving cache directories:")
        for cache_dir in sorted(cache_dirs):
            print(f"  - {cache_dir}")
            shutil.rmtree(cache_dir)
    else:
        print("\nNo cache directories found.")

    # Find and remove temporary files
    temp_files = find_temp_files(root)
    if temp_files:
        print("\nRemoving temporary files:")
        for temp_file in sorted(temp_files):
            print(f"  - {temp_file}")
            temp_file.unlink()
    else:
        print("\nNo temporary files found.")

    # Clean up coverage data
    coverage_file = root / ".coverage"
    if coverage_file.exists():
        print(f"\nRemoving coverage data: {coverage_file}")
        coverage_file.unlink()

    print("\n✅ Cleanup complete!")


if __name__ == "__main__":
    main() 