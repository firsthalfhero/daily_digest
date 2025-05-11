"""Script to create the environment template file."""

from pathlib import Path
from src.utils.config import create_config_template


def main():
    """Create the environment template file."""
    print("Creating environment template...")
    create_config_template()
    print("Done! Please copy .env.template to .env and fill in your values.")


if __name__ == "__main__":
    main() 