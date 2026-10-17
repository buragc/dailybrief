# Daily Brief

A daily scheduled task that collects articles/news updates/other info from configured sources, creates an epub, and sends it to your Kindle for reading on your commute.

## Sources

- **Hacker News**: Top stories via API
- **Stocks**: Market data from Yahoo Finance (DUOL, MSFT, APPL, SMH, XLK, BUG, NVDA, ARM, MRVL, TEM)
- **News**: sozcu.com.tr, duhuliye.com, marketwatch.com, reuters.com
- **RSS**: NFL, NBA, EPL updates
- **X/Twitter**: Timeline posts with ad/repetitive content filtering
- **Financial Times**: Browser scraping (optional, behind login)

## Setup

```bash
cd ~/dev/dailybrief
pip install -r requirements.txt
```

## Configuration

Edit `config.yaml` to enable/disable sources, adjust counts, change topics, etc.

## Usage

```bash
python dailybrief.py
```

## Delivery

The epub is:
1. Saved locally to `output/` directory
2. Sent via Gmail SMTP to your Kindle email address

## Scheduling

Set up via Hermes cron:
```
0 7 * * *  # Every day at 7 AM
```

## Project Structure

```
dailybrief/
├── config.yaml          # Configuration file
├── .env                 # Environment variables (GMAIL_APP_PASSWORD)
├── .gitignore
├── dailybrief.py        # Entry point
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── config.py        # Config loading
│   ├── models.py        # Article dataclass, SourceCollector base
│   ├── hackernews_collector.py
│   ├── stock_collector.py
│   ├── news_collector.py
│   ├── rss_collector.py
│   ├── x_twitter_collector.py
│   ├── epub_builder.py  # Epub generation
│   ├── email_sender.py  # Email delivery
│   ├── env_loader.py
│   └── orchestrator.py  # Main pipeline
```

A daily brief project.
