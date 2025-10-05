#!/usr/bin/env python3
"""
Helyxium - Universal VR Bridge Platform
Where the World Comes Together

Main application entry point.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.application import HelyxiumApp


def main() -> int:
    """Main application entry point."""
    app = HelyxiumApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())