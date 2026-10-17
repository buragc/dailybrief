"""Collects news from various sources using web scraping."""

from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup

from .models import Article, SourceCollector


class NewsCollector(SourceCollector):
    """Collects news from configurable web sources."""

    SOURCES = {
        "sozcu.com.tr": {
            "url": "https://www.sozcu.com.tr/ekonomi/",
            "selectors": [
                ("h3", "title"),
                ("a", "link"),
                ("p", "summary"),
            ],
            "fallback_title": "Sozcu Economy",
            "fallback_url": "https://www.sozcu.com.tr",
        },
        "duhuliye.com": {
            "url": "https://www.duhuliye.com",
            "selectors": [
                ("h2", "title"),
                ("h3", "title"),
                ("a", "link"),
                ("p", "summary"),
            ],
            "fallback_title": "Duhuliye",
            "fallback_url": "https://www.duhuliye.com",
        },
        "marketwatch.com": {
            "url": "https://www.marketwatch.com/latest-news",
            "selectors": [
                ("h2", "title"),
                ("h3", "title"),
                ("h4", "title"),
                ("a", "link"),
                ("p", "summary"),
            ],
            "fallback_title": "MarketWatch",
            "fallback_url": "https://www.marketwatch.com",
        },
        "reuters.com": {
            "url": "https://www.reuters.com/business/",
            "selectors": [
                ("h2", "title"),
                ("h3", "title"),
                ("h4", "title"),
                ("a", "link"),
                ("p", "summary"),
            ],
            "fallback_title": "Reuters",
            "fallback_url": "https://www.reuters.com",
        },
    }

    def collect(self) -> List[Article]:
        news_sources = self.config.get("news", [])
        all_articles = []

        for source_config in news_sources:
            source_name = source_config.get("source", "")
            language = source_config.get("language", "en")
            source_info = self.SOURCES.get(source_name)
            if not source_info:
                continue

            articles = self._scrape_source(source_name, source_info, language)
            all_articles.extend(articles)

        return all_articles

    def _scrape_source(self, source_name: str, source_info: dict, language: str) -> List[Article]:
        """Scrape a single news source."""
        url = source_info["url"]
        selectors = source_info["selectors"]
        fallback_title = source_info["fallback_title"]
        fallback_url = source_info["fallback_url"]

        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            return [Article(
                title=f"{fallback_title}",
                summary=f"Failed to fetch: {e}",
                source=fallback_title,
                topic="Finance & Markets",
                language=language,
            )]

        articles = []
        # Find all article-like elements
        for tag, cls in selectors:
            elements = soup.find_all(tag)
            for elem in elements:
                title_elem = elem.find(class_=cls) if cls else elem
                if not title_elem:
                    title_elem = elem

                text = title_elem.get_text(strip=True) if title_elem else ""
                if not text or len(text) < 10:
                    continue

                # Get link if available
                link_elem = elem.find("a", href=True)
                link = link_elem["href"] if link_elem else fallback_url

                # Get summary if available
                summary_elem = elem.find("p")
                summary = summary_elem.get_text(strip=True) if summary_elem else text[:200]

                if text:
                    articles.append(Article(
                        title=text,
                        summary=summary,
                        source=fallback_title,
                        topic="Finance & Markets",
                        url=link,
                        language=language,
                    ))

        # Deduplicate by title
        seen = set()
        unique_articles = []
        for article in articles:
            if article.title not in seen:
                seen.add(article.title)
                unique_articles.append(article)

        return unique_articles[:5]  # Limit per source
