"""Collects top stories from Hacker News."""

from datetime import datetime
from typing import List
import json
import urllib.request
import urllib.error

from .models import Article, SourceCollector


class HackerNewsCollector(SourceCollector):
    """Collects top stories from Hacker News API."""

    def collect(self) -> List[Article]:
        count = self.config.get("count", 10)
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                story_ids = json.loads(resp.read().decode())[:count]
        except Exception as e:
            raise ConnectionError(f"HN API failed: {e}")

        articles = []
        for story_id in story_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            try:
                with urllib.request.urlopen(story_url, timeout=15) as resp:
                    story = json.loads(resp.read().decode())
            except Exception:
                continue

            title = story.get("title", "Untitled")
            link = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
            score = story.get("score", 0)
            num_comments = story.get("descendants", 0)

            # Summary: extract from text if available, else use score + comments as proxy
            text = story.get("text", "")
            if text:
                # Get first paragraph, stripped
                summary = text.split('\n\n')[0].strip()[:300]
            else:
                summary = f"{score} points, {num_comments} comments"

            articles.append(Article(
                title=title,
                summary=summary,
                source="Hacker News",
                topic="AI & Tech",
                url=link,
                date=datetime.fromtimestamp(story.get("time", 0)) if story.get("time") else None,
            ))

        return articles
