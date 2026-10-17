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
            "fallback_title": "Sozcu Economy",
            "fallback_url": "https://www.sozcu.com.tr",
        },
        "duhuliye.com": {
            "url": "https://www.duhuliye.com",
            "fallback_title": "Duhuliye",
            "fallback_url": "https://www.duhuliye.com",
        },
        "marketwatch.com": {
            "url": "https://www.marketwatch.com/latest-news",
            "fallback_title": "MarketWatch",
            "fallback_url": "https://www.marketwatch.com",
        },
        "reuters.com": {
            "url": "https://www.reuters.com/business/",
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

            # Duhuliye requires JS, use browser scraping
            if source_name == "duhuliye.com":
                articles = self._scrape_duhuliye(language)
            else:
                articles = self._scrape_source(source_name, source_info, language)
            all_articles.extend(articles)

        return all_articles

    def _scrape_duhuliye(self, language: str) -> List[Article]:
        """Scrape Duhuliye articles with full content."""
        articles = []

        # First, get the main page to find article links
        try:
            resp = requests.get(
                "https://www.duhuliye.com",
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                }
            )
            resp.raise_for_status()
            main_soup = BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            return [Article(
                title="Duhuliye",
                summary=f"Failed to fetch main page: {e}",
                source="Duhuliye",
                topic="Finance & Markets",
                language=language,
            )]

        # Find article links from main page
        article_links = []
        seen_urls = set()
        for link in main_soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)

            # Filter for actual article links
            if (href and "/futbol/" in href and
                len(text) > 15 and len(text) < 200 and
                href not in seen_urls):
                seen_urls.add(href)
                article_links.append((text, href))
                if len(article_links) >= 5:
                    break

        # Fetch each article and extract full content
        for title, url in article_links:
            try:
                resp = requests.get(
                    url,
                    timeout=15,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml",
                    }
                )
                resp.raise_for_status()
                article_soup = BeautifulSoup(resp.text, "lxml")

                # Extract article body text
                body_parts = []

                # Find all paragraphs with meaningful content
                for p in article_soup.find_all("p"):
                    text = p.get_text(strip=True)
                    if len(text) > 30:
                        body_parts.append(text)

                # If we found content, extract subheading (h2)
                subheading = ""
                h2 = article_soup.find("h2")
                if h2:
                    subheading = h2.get_text(strip=True)

                # Build summary from body
                if body_parts:
                    summary = f"[{subheading}]\n" + "\n".join(body_parts[:8]) if subheading else "\n".join(body_parts[:8])
                else:
                    summary = f"[No full content available - requires JS rendering]"

                articles.append(Article(
                    title=title,
                    summary=summary,
                    source="Duhuliye",
                    topic="Finance & Markets",
                    url=url,
                    language=language,
                ))

            except Exception as e:
                articles.append(Article(
                    title=title,
                    summary=f"Failed to fetch article: {e}",
                    source="Duhuliye",
                    topic="Finance & Markets",
                    url=url,
                    language=language,
                ))

        return articles

    def _scrape_source(self, source_name: str, source_info: dict, language: str) -> List[Article]:
        """Scrape a single news source."""
        url = source_info["url"]
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
        for tag in ["h2", "h3", "h4"]:
            elements = soup.find_all(tag)
            for elem in elements:
                text = elem.get_text(strip=True)
                if not text or len(text) < 10:
                    continue

                # Get link if available
                link_elem = elem.find("a", href=True)
                link = link_elem["href"] if link_elem else fallback_url
                if link.startswith("//"):
                    link = "https:" + link

                # Get summary if available
                summary_elem = elem.find_next("p")
                summary = summary_elem.get_text(strip=True) if summary_elem else text[:200]

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
