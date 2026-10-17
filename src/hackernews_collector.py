"""Collects top stories from Hacker News with article content and comment summaries."""

from datetime import datetime
from typing import List, Tuple
import json
import urllib.request
import urllib.error
import requests
from bs4 import BeautifulSoup

from .models import Article, SourceCollector


class HackerNewsCollector(SourceCollector):
    """Collects top stories from Hacker News API with article content and comment insights."""

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
            try:
                article, comment_insights = self._fetch_story_with_comments(story_id)
                article.source = "Hacker News (Article + Comments)"
                articles.append(article)
            except Exception as e:
                print(f"  [skip] Story {story_id} failed: {e}")
                continue

        return articles

    def _fetch_story_with_comments(self, story_id: int) -> Tuple[Article, List[str]]:
        """Fetch a single HN story with article content and comment insights."""
        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        try:
            with urllib.request.urlopen(story_url, timeout=15) as resp:
                story = json.loads(resp.read().decode())
        except Exception:
            raise ConnectionError(f"Failed to fetch story {story_id}")

        title = story.get("title", "Untitled")
        link = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
        score = story.get("score", 0)
        num_comments = story.get("descendants", 0)
        text = story.get("text", "")

        # Fetch article content from URL
        article_content = ""
        if link and not link.startswith("https://news.ycombinator.com/"):
            article_content = self._fetch_article_content(link)

        # Fetch top comments and generate insights
        comment_insights = self._get_comment_insights(story)

        # Build summary: article content + comment insights
        summary_parts = []
        if article_content:
            summary_parts.append(f"[Article Summary]\n{article_content}")
        else:
            summary_parts.append(f"[Story Details]\n{score} points, {num_comments} comments")

        if text:
            summary_parts.append(f"[Submission Text]\n{text[:500]}")

        if comment_insights:
            # Format comment insights as HTML bullet points
            comment_li = "".join(f"<li>{ins}</li>" for ins in comment_insights[:10])
            summary_parts.append(f"<h3>Top {len(comment_insights)} Comment Insights</h3><ul>{comment_li}</ul>")

        summary = "\n\n".join(summary_parts)

        return Article(
            title=title,
            summary=summary,
            source="Hacker News",
            topic="AI & Tech",
            url=link,
            date=datetime.fromtimestamp(story.get("time", 0)) if story.get("time") else None,
        ), comment_insights

    def _fetch_article_content(self, url: str, max_chars: int = 1500) -> str:
        """Fetch and extract article content from a URL."""
        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Try to find main content
            candidates = [
                soup.find("article"),
                soup.find("main"),
                soup.find(class_=lambda c: c and "content" in c.lower()),
                soup.find(id=lambda i: i and "content" in i.lower()),
            ]

            content_elem = None
            for candidate in candidates:
                if candidate:
                    content_elem = candidate
                    break

            if not content_elem:
                content_elem = soup.find("body")

            if content_elem:
                paragraphs = content_elem.find_all("p")
                if paragraphs:
                    content_parts = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if len(text) > 20:
                            content_parts.append(text)

                    content = " ".join(content_parts[:20])
                    if len(content) > max_chars:
                        content = content[:max_chars] + "..."
                    return content

            return f"Article at {url}"
        except Exception as e:
            return f"Could not fetch article content ({e})"

    def _get_comment_insights(self, story: dict, max_top_comments: int = 10) -> List[str]:
        """Fetch top-level comments and extract key insights."""
        top_comment_ids = story.get('kids', [])[:max_top_comments]
        if not top_comment_ids:
            return []

        comments = []
        for cid in top_comment_ids[:max_top_comments]:
            comment_url = f"https://hacker-news.firebaseio.com/v0/item/{cid}.json"
            try:
                with urllib.request.urlopen(comment_url, timeout=10) as resp:
                    comment = json.loads(resp.read().decode())
                    # Only include comments with meaningful text
                    text = comment.get('text', '').strip()
                    if len(text) > 30:
                        comments.append({
                            'by': comment.get('by', 'unknown'),
                            'text': text,
                            'kids': len(comment.get('kids', [])),
                            'score': comment.get('score', 0)
                        })
            except:
                pass

        # Sort by score/replies to get most valuable comments
        comments.sort(key=lambda c: c['kids'] + c['score'], reverse=True)

        # Extract top insights (first 10 most engaged comments)
        insights = []
        for c in comments[:10]:
            insight = f"@{c['by']}: {c['text'][:250]}"
            if c['kids'] > 0:
                insight += f" ({c['kids']} replies)"
            insights.append(insight)

        return insights
