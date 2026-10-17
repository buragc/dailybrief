from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import yaml


@dataclass
class SourceConfig:
    """Top-level source configuration."""
    hackernews: dict = field(default_factory=dict)
    x_twitter: dict = field(default_factory=dict)
    stocks: dict = field(default_factory=dict)
    news: List[dict] = field(default_factory=list)
    ft: dict = field(default_factory=dict)
    rss: dict = field(default_factory=dict)
    watchexchange: dict = field(default_factory=dict)


@dataclass
class DeliveryConfig:
    """Email delivery configuration."""
    kindle_email: str = ""
    sender_email: str = ""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587


@dataclass
class EpubConfig:
    """Epub generation configuration."""
    title_prefix: str = "Daily Brief"
    topic_order: List[str] = field(default_factory=list)
    output_dir: str = "output"


@dataclass
class AppConfig:
    """Full application configuration."""
    sources: SourceConfig = field(default_factory=SourceConfig)
    delivery: DeliveryConfig = field(default_factory=DeliveryConfig)
    epub: EpubConfig = field(default_factory=EpubConfig)


def load_config(path: Optional[str] = None) -> AppConfig:
    """Load configuration from YAML file."""
    if path is None:
        path = str(Path(__file__).parent.parent / "config.yaml")
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return AppConfig(
        sources=SourceConfig(**data.get("source", {})),
        delivery=DeliveryConfig(**data.get("delivery", {})),
        epub=EpubConfig(**data.get("epub", {})),
    )
