"""
Social Listener Runner - Continuous Monitoring
"""
import time
from x_snscrape import fetch_by_hashtag, push_to_redis, SL_HASHTAGS, SNSCRAPE_AVAILABLE

def run_collection_cycle(max_tweets_per_tag=30):
    """Execute one social media collection cycle"""
    print("\n" + "="*60)
    print(f"SOCIAL LISTENING CYCLE")
    print("="*60)
    
    if not SNSCRAPE_AVAILABLE:
        print("snscrape not available - skipping")
        return
    
    total_tweets = 0
    
    for hashtag in SL_HASHTAGS:
        try:
            items = fetch_by_hashtag(hashtag, max_tweets=max_tweets_per_tag)
            
            for item in items:
                push_to_redis(item)
            
            total_tweets += len(items)
            time.sleep(5)  # Rate limiting between hashtags
            
        except Exception as e:
            print(f"❌ Error with #{hashtag}: {e}")
    
    print(f"\nCycle complete: {total_tweets} total tweets")
    print("="*60)

def main_loop(interval_minutes=15):
    """
    Main loop for social listening
    
    Args:
        interval_minutes: Minutes between collection cycles
    """
    print("="*60)
    print("🐦 SOCIAL LISTENER STARTED")
    print("="*60)
    print(f"Interval: {interval_minutes} minutes")
    print(f"Hashtags: {', '.join(['#' + h for h in SL_HASHTAGS])}")
    print(f"Output: Redis queue 'collector:incoming'")
    print("="*60)
    print("Press Ctrl+C to stop\n")
    
    while True:
        try:
            run_collection_cycle()
            print(f"\n⏳ Waiting {interval_minutes} minutes until next cycle...\n")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n\n👋 Social listener stopped")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop(interval_minutes=15)