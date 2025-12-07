"""
Database monitoring utility
Shows real-time statistics
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pipeline.models.database import Database
from datetime import datetime
import time

def display_stats():
    """Display comprehensive database statistics"""
    db = Database()
    
    if not db.connect():
        print(" Cannot connect to database")
        return
    
    while True:
        # Clear screen (Windows)
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        

        print(f" LAYER 2 - DATABASE MONITOR")
        print(f"   Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        stats = db.get_statistics()
        
        # Overall stats
        print(f"\n📈 OVERALL STATISTICS")
        print(f"{'─'*70}")
        print(f"  Total Records:     {stats.get('total_records', 0):,}")
        print(f"  News Articles:     {stats.get('by_type', {}).get('news', 0):,}")
        print(f"  Social Posts:      {stats.get('by_type', {}).get('social', 0):,}")
        print(f"  Last 24 Hours:     {stats.get('last_24h', 0):,}")
        
        # By source
        if stats.get('by_source'):
            print(f"\n BY SOURCE")
            print(f"{'─'*70}")
            for source, count in stats['by_source'].items():
                bar = "█" * min(50, count // 10)
                print(f"  {source:30} {count:5,} {bar}")
        
        # Top topics
        if stats.get('top_topics'):
            print(f"\n TOP TOPICS (Last 24h)")
            print(f"{'─'*70}")
            for topic, count in stats['top_topics'].items():
                print(f"  • {topic:30} {count:3} mentions")
        
        # Hourly rate
        hourly = db.get_hourly_collection_rate()
        if hourly:
            print(f"\n COLLECTION RATE (Last 24h)")
            print(f"{'─'*70}")
            for row in hourly[:5]:
                hour = row['hour'].strftime('%Y-%m-%d %H:00')
                print(f"  {hour} | {row['source_type']:8} | {row['count']:4} items")
        
        print(f"\n{'='*70}")
        print(f" Refreshing in 10 seconds... (Ctrl+C to stop)")
        print(f"{'='*70}\n")
        
        time.sleep(10)

if __name__ == "__main__":
    try:
        display_stats()
    except KeyboardInterrupt:
        print("\n\n Monitor stopped")