"""
Generic RSS Feed Scraper with Redis Queue
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from langdetect import detect, LangDetectException
import json
import redis
import time
from datetime import datetime

REDIS_KEY = "collector:incoming"

# Initialize Redis connection
try:
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    r.ping()
    print("Connected to Redis")
except redis.ConnectionError:
    print("Redis not available. Start with: docker compose up -d")
    r = None

def fetch_rss_feed(url, source_name):
    """
    Fetch RSS feed and extract articles
    
    Args:
        url: RSS feed URL
        source_name: Name of the source (e.g., "Daily Mirror")
    
    Returns:
        List of normalized article dictionaries
    """
    print(f"📰 Fetching {source_name}...")
    
    feed = feedparser.parse(url)
    items = []
    
    for entry in feed.entries[:20]:  # Limit to 20 articles
        title = entry.get("title", "")
        link = entry.get("link", "")
        published = entry.get("published", entry.get("updated", ""))
        
        # Parse published date
        try:
            published_iso = dateparser.parse(published).isoformat()
        except Exception:
            published_iso = datetime.utcnow().isoformat()

        # Try to fetch article snippet (conservative scraping)
        snippet = ""
        try:
            resp = requests.get(
                link, 
                timeout=8, 
                headers={"User-Agent": "ModelXBot/1.0 (Educational Project)"}
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Extract first few paragraphs
            paragraphs = soup.find_all("p")
            if paragraphs:
                snippet = " ".join([p.get_text().strip() for p in paragraphs[:3]])
        except Exception as e:
            # If scraping fails, use RSS summary
            snippet = entry.get("summary", "")

        # Detect language
        language = None
        try:
            text_to_detect = (title + " " + snippet).strip()
            if text_to_detect:
                language = detect(text_to_detect)
        except LangDetectException:
            language = "unknown"

        # Create normalized item
        item = {
            "source": source_name,
            "source_type": "news",
            "url": link,
            "title": title,
            "snippet": snippet[:800],  # Limit snippet length
            "published": published_iso,
            "fetched_at": datetime.utcnow().isoformat(),
            "language": language,
            "collector": "news_scraper"
        }
        items.append(item)
    
    print(f"Fetched {len(items)} articles from {source_name}")
    return items

def push_to_redis(item):
    """Push normalized item to Redis queue"""
    if r:
        r.rpush(REDIS_KEY, json.dumps(item, ensure_ascii=False))
    else:
        # Fallback: save to file
        save_to_file(item)

def save_to_file(item):
    """Fallback: Save to JSON file if Redis unavailable"""
    from pathlib import Path
    
    output_dir = Path("data_output/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = output_dir / f"news_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

# Sri Lankan news sources
SL_NEWS_SOURCES = {
    'Ada Derana': 'http://www.adaderana.lk/rss.php',
    'The Island': 'http://island.lk/feed/',
}
