"""Collects Twitter/X posts from the user's timeline."""

from typing import List

from .models import Article, SourceCollector


class XTwitterCollector(SourceCollector):
    """Collects posts from X/Twitter timeline."""

    def collect(self) -> List[Article]:
        # Use the xurl CLI tool (pre-installed in the system)
        import subprocess

        count = self.config.get("count", 50)
        skip_ads = self.config.get("skip_ads", True)
        skip_repetitive = self.config.get("skip_repetitive", True)

        try:
            # Get timeline tweets using xurl
            result = subprocess.run(
                ["xurl", "timeline", "--count", str(count)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(f"xurl failed: {result.stderr}")

            raw_tweets = result.stdout.strip().split('\n')
            tweets = []
            seen_texts = set()

            for line in raw_tweets:
                if not line.strip():
                    continue

                # Skip ads
                if "promoted" in line.lower() or "ad" in line.lower():
                    continue

                # Skip repetitive content
                if skip_repetitive:
                    # Extract main text (simplified dedup)
                    text = line.split('|')[0] if '|' in line else line[:100]
                    if text in seen_texts:
                        continue
                    seen_texts.add(text)

                # Parse tweet line (format: user | text | timestamp)
                parts = line.split('|')
                user = parts[0].strip() if len(parts) > 0 else "Unknown"
                text = parts[1].strip() if len(parts) > 1 else line
                timestamp = parts[2].strip() if len(parts) > 2 else ""

                # Extract link if present
                url = None
                if "http" in line:
                    for word in line.split():
                        if word.startswith("http"):
                            url = word
                            break

                tweets.append(Article(
                    title=f"@{user}",
                    summary=text,
                    source="X / Twitter",
                    topic="X / Twitter",
                    url=url,
                ))

            return tweets[:count]

        except FileNotFoundError:
            raise RuntimeError("xurl CLI not found - install it first")
        except Exception as e:
            raise RuntimeError(f"Failed to collect X timeline: {e}")
