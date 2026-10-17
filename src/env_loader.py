"""Load environment variables from .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_env():
    """Load .env file from project root."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[env] Loaded {env_path}")
    else:
        print("[env] No .env file found, using system env vars")
