#!/usr/bin/env python3

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli import YouTubeMigratorCLI


def main():
    try:
        cli = YouTubeMigratorCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()