"""Daily Brief — Main entry point."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import run

if __name__ == "__main__":
    run()
