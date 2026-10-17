"""Build and write epub files for Daily Brief."""

from datetime import datetime
from pathlib import Path
from typing import List

from ebooklib import epub

from .models import Article


class EpubBuilder:
    """Builds an epub file from a list of articles grouped by topic."""

    def __init__(self, config: dict):
        self.title_prefix = config.title_prefix
        self.topic_order = config.topic_order

    def build(self, articles: List[Article], output_dir: str = "output") -> str:
        """Build an epub file and return its path."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        epub_name = f"{self.title_prefix.replace(' ', '_')}_{date_str}.epub"
        output_path = Path(output_dir) / epub_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create epub book
        book = epub.EpubBook()

        # Metadata
        book.set_identifier(f"dailybrief-{date_str}")
        book.set_title(f"{self.title_prefix} — {date_str}")
        book.set_language("en")
        book.add_author("Daily Brief")

        # Group articles by topic
        topic_groups = {}
        for article in articles:
            topic = article.topic
            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append(article)

        # Sort topics by configured order
        sorted_topics = []
        for topic in self.topic_order:
            if topic in topic_groups:
                sorted_topics.append(topic)
        for topic in topic_groups:
            if topic not in sorted_topics:
                sorted_topics.append(topic)

        # Add master index chapter first (all headlines)
        index_html = self._create_index_html(articles)
        index_chapter = epub.EpubHtml(
            title="All Headlines",
            file_name="index.xhtml",
            lang="en",
        )
        index_chapter.content = index_html.encode("utf-8")
        book.add_item(index_chapter)

        # Add chapter content
        nav_items = [index_chapter]
        for topic in sorted_topics:
            topic_articles = topic_groups[topic]
            chapter_html = self._create_topic_html(topic, topic_articles)

            chapter = epub.EpubHtml(
                title=topic,
                file_name=f"topic_{topic.replace(' ', '_')}.xhtml",
                lang="en",
            )
            chapter.content = chapter_html.encode("utf-8")
            book.add_item(chapter)
            nav_items.append(chapter)

        # Table of contents
        book.toc = nav_items

        # Navigation
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Spine
        book.spine = ["nav"] + nav_items

        # Write epub file
        epub.write_epub(str(output_path), book)

        return str(output_path)

    def _create_topic_html(self, topic: str, articles: List[Article]) -> str:
        """Create HTML content for a topic section."""
        html = f"<h1>{topic}</h1>"

        for article in articles:
            # Regular article with URL
            url_attr = f'href="{article.url}"' if article.url else ""
            html += f'<h2 {url_attr}>{article.title}</h2>'
            html += f'<p>{article.summary}</p>'
            if article.source:
                html += f'<p><small>Source: {article.source}</small></p>'

        return "<html><body>" + html + "</body></html>"

    def _create_index_html(self, articles: List[Article]) -> str:
        """Create master index page listing all headlines across all topics."""
        html = "<h1>Daily Brief — All Headlines</h1><ul>"
        for article in articles:
            url_attr = f'href="{article.url}"' if article.url else ""
            html += f'<li><a {url_attr}>{article.title}</a> — <em>{article.topic}</em></li>'
        html += "</ul>"
        return "<html><body>" + html + "</body></html>"
