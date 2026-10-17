"""Source modules for Daily Brief.

Each module is responsible for collecting content from a specific source
and returning a list of Article objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Article:
    """Represents a single article or content item."""
    title: str
    summary: str
    source: str
    topic: str
    url: Optional[str] = None
    date: Optional[datetime] = None
    language: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class SourceCollector:
    """Base class for source collectors."""

    def __init__(self, config: dict, source_name: str):
        self.config = config
        self.name = source_name

    def collect(self) -> List[Article]:
        """Collect articles from this source."""
        raise NotImplementedError

    def collect_with_retry(self, max_retries: int = 1) -> List[Article]:
        """Collect with retry logic."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return self.collect()
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    print(f"  [retry {attempt+1}/{max_retries}] {self.name} failed: {e}")
        print(f"  [skip] {self.name} failed after {max_retries+1} attempts: {last_error}")
        return []
