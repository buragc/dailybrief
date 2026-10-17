"""Collects stock data using Yahoo Finance in table format."""

from typing import List

import requests

from .models import Article, SourceCollector


class StockCollector(SourceCollector):
    """Collects stock market data from Yahoo Finance and returns as table-ready data."""

    def collect(self) -> List[Article]:
        tickers = self.config.get("tickers", [])
        stock_data = []

        for ticker in tickers:
            try:
                yfinance_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
                params = {"interval": "1d", "range": "1d"}
                resp = requests.get(yfinance_url, params=params, timeout=15, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                })
                resp.raise_for_status()
                data = resp.json()

                result = data.get("chart", {}).get("result", [{}])[0]
                meta = result.get("meta", {})
                symbol = meta.get("symbol", ticker)
                price = meta.get("regularMarketPrice", "N/A")
                prev_close = meta.get("chartPreviousClose", price)

                if isinstance(prev_close, (int, float)) and isinstance(price, (int, float)):
                    change = price - prev_close
                    change_pct = (change / prev_close) * 100
                    price_str = f"${price:.2f}"
                    change_str = f"{change:+.2f}"
                    change_pct_str = f"{change_pct:+.2f}%"
                else:
                    price_str = str(price)
                    change_str = "N/A"
                    change_pct_str = "N/A"

                stock_data.append({
                    "ticker": symbol,
                    "price": price_str,
                    "change": change_str,
                    "change_pct": change_pct_str,
                })

            except Exception as e:
                stock_data.append({
                    "ticker": ticker,
                    "price": "N/A",
                    "change": "N/A",
                    "change_pct": str(e)[:30],
                })

        # Return as a single article with plain text stock data
        text_body = self._format_stock_data(stock_data)
        return [Article(
            title="Stock Market Performance",
            summary=text_body,
            source="Yahoo Finance",
            topic="Finance & Markets",
        )]

    def _format_stock_data(self, stock_data: List[dict]) -> str:
        """Format stock data as plain text (no HTML tables)."""
        lines = []
        for stock in stock_data:
            color = "+" if stock["change"].startswith("+") else ""
            lines.append(f"{stock['ticker']:6s}  {stock['price']:10s}  {color}{stock['change']:>8s}  {stock['change_pct']}")

        return "Stock  Price        Change    Chg%\n" + "\n".join(lines)
