"""Daily Brief: Orchestrates collection, building, and delivery."""

import sys
from pathlib import Path
from datetime import datetime

from .config import load_config
from .models import Article
from .hackernews_collector import HackerNewsCollector
from .stock_collector import StockCollector
from .news_collector import NewsCollector
from .rss_collector import RSSCollector
from .x_twitter_collector import XTwitterCollector
from .epub_builder import EpubBuilder
from .email_sender import EmailSender
from .env_loader import load_env

# Register all collectors
COLLECTORS = {
    "hackernews": HackerNewsCollector,
    "stocks": StockCollector,
    "news": NewsCollector,
    "rss": RSSCollector,
    "x_twitter": XTwitterCollector,
}


def collect_all(config) -> list[Article]:
    """Run all enabled collectors and return sorted articles."""
    print("=" * 60)
    print("DAILY BRIEF — Collection Phase")
    print("=" * 60)

    articles = []

    # 1. Hacker News
    hn_cfg = config.sources.hackernews
    if hn_cfg.get("enabled", True):
        print("\n[1/5] Collecting Hacker News...")
        collector = HackerNewsCollector(hn_cfg, "hackernews")
        articles.extend(collector.collect_with_retry(max_retries=1))

    # 2. Stocks
    stock_cfg = config.sources.stocks
    if stock_cfg.get("enabled", True):
        print("\n[2/5] Collecting Stock Data...")
        collector = StockCollector(stock_cfg, "stocks")
        articles.extend(collector.collect_with_retry(max_retries=1))

    # 3. News
    news_cfg = config.sources.news
    if news_cfg:
        print("\n[3/5] Collecting News Sources...")
        collector = NewsCollector({"news": news_cfg}, "news")
        articles.extend(collector.collect_with_retry(max_retries=1))

    # 4. RSS feeds
    rss_cfg = config.sources.rss
    if rss_cfg:
        print("\n[4/5] Collecting RSS Feeds...")
        collector = RSSCollector({"rss": rss_cfg}, "rss")
        articles.extend(collector.collect_with_retry(max_retries=1))

    # 5. X/Twitter
    x_cfg = config.sources.x_twitter
    if x_cfg.get("enabled", True):
        print("\n[5/5] Collecting X/Twitter Timeline...")
        collector = XTwitterCollector(x_cfg, "x_twitter")
        articles.extend(collector.collect_with_retry(max_retries=1))

    print(f"\n✓ Total articles collected: {len(articles)}")
    return articles


def build_epub(articles: list[Article], config) -> str:
    """Build epub file from articles."""
    print("\n" + "=" * 60)
    print("DAILY BRIEF — Epub Generation")
    print("=" * 60)

    epub_cfg = config.epub
    builder = EpubBuilder(epub_cfg)
    epub_path = builder.build(articles, output_dir=epub_cfg.output_dir)
    print(f"✓ Epub saved: {epub_path}")
    return epub_path


def send_email(epub_path: str, config) -> bool:
    """Send epub via email to Kindle."""
    print("\n" + "=" * 60)
    print("DAILY BRIEF — Email Delivery")
    print("=" * 60)

    sender = EmailSender(config.delivery)
    sender.send(epub_path)
    print(f"✓ Epub sent to Kindle: {config.delivery.kindle_email}")
    return True


def run():
    """Run the full Daily Brief pipeline."""
    print("Starting Daily Brief...")
    load_env()

    # Load config
    config = load_config()

    # Phase 1: Collect
    articles = collect_all(config)

    if not articles:
        print("No articles collected — skipping epub generation")
        return

    # Phase 2: Build
    epub_path = build_epub(articles, config)

    # Phase 3: Send
    send_email(epub_path, config)

    print("\n" + "=" * 60)
    print("DAILY BRIEF — COMPLETE ✓")
    print("=" * 60)


if __name__ == "__main__":
    run()
