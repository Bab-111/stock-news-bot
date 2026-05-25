import yfinance as yf
import feedparser
from datetime import datetime
from pathlib import Path

STOCKS = Path("stocks.txt").read_text().strip().splitlines()

GENERAL_NEWS_FEEDS = [
    ("Reuters Markets",    "https://feeds.reuters.com/reuters/businessNews"),
    ("MarketWatch",        "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"),
    ("CNBC",               "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    ("Google Finance News","https://news.google.com/rss/search?q=stock+market+finance&hl=en-US&gl=US&ceid=US:en"),
]

def get_general_news():
    all_news = []
    for source_name, url in GENERAL_NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:3]:
                all_news.append({
                    "source": source_name,
                    "title": e.title,
                    "link": e.link,
                    "published": e.get("published", "")[:16]
                })
        except:
            pass
    return all_news[:12]  # Show top 12 general news items

def get_yahoo_news(ticker):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    feed = feedparser.parse(url)
    return [
        {"title": e.title, "link": e.link, "published": e.get("published", "")[:16]}
        for e in feed.entries[:5]
    ]

def get_stock_info(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="2d")
        price = hist["Close"].iloc[-1] if not hist.empty else None
        prev  = hist["Close"].iloc[-2] if len(hist) > 1 else price
        change_pct = ((price - prev) / prev * 100) if price and prev else 0
        return {
            "name": info.get("longName", ticker),
            "price": round(price, 2) if price else "N/A",
            "change_pct": round(change_pct, 2),
            "sector": info.get("sector", "N/A"),
        }
    except:
        return {"name": ticker, "price": "N/A", "change_pct": 0, "sector": "N/A"}

def generate_html(data, general_news):
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    # General news section
    general_items = "".join(
        f'''<li>
              <span class="news-source">{n["source"]}</span>
              <a href="{n["link"]}" target="_blank">{n["title"]}</a>
              <small>{n["published"]}</small>
            </li>'''
        for n in general_news
    ) or "<li>No general news found</li>"

    # Stock cards
    stock_cards = ""
    for item in data:
        info = item["info"]
        color = "green" if info["change_pct"] >= 0 else "red"
        sign  = "+" if info["change_pct"] >= 0 else ""
        news_html = "".join(
            f'<li><a href="{n["link"]}" target="_blank">{n["title"]}</a> <small>{n["published"]}</small></li>'
            for n in item["news"]
        ) or "<li>No news found</li>"
        stock_cards += f"""
        <div class="card">
          <div class="card-header">
            <span class="ticker">{item['ticker']}</span>
            <span class="name">{info['name']}</span>
            <span class="price">${info['price']}</span>
            <span class="change" style="color:{color}">{sign}{info['change_pct']}%</span>
          </div>
          <div class="meta">Sector: {info['sector']}</div>
          <ul class="news-list">{news_html}</ul>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Stock News Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }}
    h1 {{ color: #1a1a2e; }}
    h2 {{ color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; margin-top: 40px; }}
    small {{ color: #999; font-size: 0.8em; margin-left: 8px; }}
    .card {{ background: white; border-radius: 10px; padding: 20px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .card-header {{ display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }}
    .ticker {{ font-size: 1.4em; font-weight: 700; color: #1a1a2e; }}
    .name {{ color: #555; flex: 1; }}
    .price {{ font-size: 1.2em; font-weight: 600; }}
    .change {{ font-weight: 600; }}
    .meta {{ color: #888; font-size: 0.85em; margin-bottom: 10px; }}
    .news-list {{ padding-left: 18px; }}
    .news-list li {{ margin: 8px 0; }}
    .news-list a {{ color: #0066cc; text-decoration: none; }}
    .news-list a:hover {{ text-decoration: underline; }}
    .general-news {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .general-news ul {{ padding-left: 0; list-style: none; }}
    .general-news li {{ padding: 10px 0; border-bottom: 1px solid #f0f0f0; }}
    .general-news a {{ color: #0066cc; text-decoration: none; font-weight: 500; }}
    .general-news a:hover {{ text-decoration: underline; }}
    .news-source {{ display: inline-block; background: #1a1a2e; color: white; font-size: 0.7em; padding: 2px 7px; border-radius: 4px; margin-right: 8px; vertical-align: middle; }}
    footer {{ text-align: center; color: #aaa; margin-top: 40px; font-size: 0.85em; }}
  </style>
</head>
<body>
  <h1>📈 Stock News Report</h1>
  <p style="color:#666">Generated: {now} &nbsp;|&nbsp; Stocks tracked: {len(data)}</p>

  <h2>🌍 General Market News</h2>
  <div class="general-news">
    <ul>{general_items}</ul>
  </div>

  <h2>📊 Your Stocks</h2>
  {stock_cards}

  <footer>Auto-generated by GitHub Actions · Sources: Yahoo Finance, Reuters, MarketWatch, CNBC, Google News</footer>
</body>
</html>"""

if __name__ == "__main__":
    print("Fetching general market news...")
    general_news = get_general_news()

    data = []
    for ticker in STOCKS:
        print(f"Processing {ticker}...")
        data.append({
            "ticker": ticker,
            "info": get_stock_info(ticker),
            "news": get_yahoo_news(ticker),
        })

    Path("report").mkdir(exist_ok=True)
    Path("report/index.html").write_text(generate_html(data, general_news))
    print("Done! Report saved to report/index.html")
