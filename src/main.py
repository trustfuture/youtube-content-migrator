#!/usr/bin/env python3

import sys

from cli import YouTubeMigratorCLI


def main() -> None:
    try:
        cli = YouTubeMigratorCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
