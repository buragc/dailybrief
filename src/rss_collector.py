"""Collects RSS feeds for sports news."""

from datetime import datetime
from typing import List

import feedparser

from .models import Article, SourceCollector


class RSSCollector(SourceCollector):
    """Collects articles from RSS feeds."""

    RSS_FEEDS = {
        "nfl": "https://www.nfl.com/news/stories.rss",
        "nba": "https://www.nba.com/rss/firstlineup.rss",
        "epl": "https://www.premierleague.com/news?rss=true",
    }

    def collect(self) -> List[Article]:
        rss_config = self.config.get("rss", {})
        all_articles = []

        for sport, feed_config in rss_config.items():
            if isinstance(feed_config, dict):
                url = feed_config.get("url", self.RSS_FEEDS.get(sport))
            else:
                url = feed_config
            if not url:
                continue

            articles = self._fetch_feed(sport, url)
            all_articles.extend(articles)

        return all_articles

    def _fetch_feed(self, sport: str, url: str) -> List[Article]:
        """Fetch a single RSS feed."""
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                return []
        except Exception as e:
            return [Article(
                title=f"{sport.upper()} RSS",
                summary=f"Failed to fetch: {e}",
                source=sport.upper(),
                topic=sport.upper(),
            )]

        articles = []
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")

            # Parse date
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])

            articles.append(Article(
                title=title,
                summary=summary[:300] if summary else title[:200],
                source=sport.upper(),
                topic=sport.upper(),
                url=link,
                date=pub_date,
            ))

        return articles[:5]  # Limit per feed
