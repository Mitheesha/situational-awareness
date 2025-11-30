"""
News Scraper Runner - Continuous Collection
Pushes articles to Redis queue
"""
import time
import sys
from pathlib import Path

# Add scrapers to path
sys.path.append(str(Path(__file__).parent))

from scrapers.generic_rss import fetch_rss_feed, push_to_redis, SL_NEWS_SOURCES

def run_collection_cycle():
    """Execute one collection cycle for all sources"""
    print("\n" + "="*60)
    print(f"NEWS COLLECTION CYCLE")
    print("="*60)
    
    total_articles = 0
    
    for source_name, feed_url in SL_NEWS_SOURCES.items():
        try:
            items = fetch_rss_feed(feed_url, source_name)
            
            for item in items:
                push_to_redis(item)
            
            total_articles += len(items)
            time.sleep(2)  # Rate limiting between sources
            
        except Exception as e:
            print(f"Error with {source_name}: {e}")
    
    print(f"\nCycle complete: {total_articles} total articles")
    print("="*60)

def main_loop(interval_minutes=10):
    """
    Main loop - runs collection at intervals
    
    Args:
        interval_minutes: Minutes between collection cycles
    """
    print("="*60)
    print("NEWS SCRAPER STARTED")
    print("="*60)
    print(f"Interval: {interval_minutes} minutes")
    print(f"Sources: {len(SL_NEWS_SOURCES)}")
    print(f"Output: Redis queue 'collector:incoming'")
    print("="*60)
    print("Press Ctrl+C to stop\n")
    
    while True:
        try:
            run_collection_cycle()
            print(f"\nWaiting {interval_minutes} minutes until next cycle...\n")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n\nNews scraper stopped")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)  # Wait 1 minute before retry

if __name__ == "__main__":
    main_loop(interval_minutes=10)