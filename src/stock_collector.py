"""Collects stock data using Yahoo Finance."""

from datetime import datetime
from typing import List

import requests

from .models import Article, SourceCollector


class StockCollector(SourceCollector):
    """Collects stock market data from Yahoo Finance."""

    def collect(self) -> List[Article]:
        tickers = self.config.get("tickers", [])
        articles = []

        for ticker in tickers:
            try:
                # Use Yahoo Finance API via requests
                yfinance_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
                params = {"interval": "1d", "range": "1d"}
                resp = requests.get(yfinance_url, params=params, timeout=15, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                })
                resp.raise_for_status()
                data = resp.json()

                # Extract price info
                result = data.get("chart", {}).get("result", [{}])[0]
                meta = result.get("meta", {})
                symbol = meta.get("symbol", ticker)
                price = meta.get("regularMarketPrice", "N/A")
            except Exception as e:
                articles.append(Article(
                    title=f"{ticker}",
                    summary=f"Failed to fetch: {e}",
                    source="Yahoo Finance",
                    topic="Finance & Markets",
                ))
                continue

            # Get previous close for change
            prev_close = meta.get("chartPreviousClose", price)
            if isinstance(prev_close, (int, float)) and isinstance(price, (int, float)):
                change = price - prev_close
                change_pct = (change / prev_close) * 100
                change_str = f"{change:+.2f} ({change_pct:+.2f}%)"
            else:
                change_str = "N/A"

            articles.append(Article(
                title=f"{symbol}",
                summary=f"${price} ({change_str})",
                source="Yahoo Finance",
                topic="Finance & Markets",
            ))

        return articles
