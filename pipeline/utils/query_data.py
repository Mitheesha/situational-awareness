"""
Quick data exploration queries
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pipeline.models.database import Database

db = Database()
if not db.connect():
    exit()

# Query examples
with db.get_cursor(dict_cursor=True) as cursor:
    
    # 1. Most urgent topics
    print("\n MOST URGENT TOPICS:")
    print("="*60)
    cursor.execute("""
        SELECT topic, urgency, COUNT(*) as count
        FROM social_posts
        WHERE urgency = 'high'
        GROUP BY topic, urgency
        ORDER BY count DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  • {row['topic']:30} {row['count']:3} mentions")
    
    # 2. Recent news headlines
    print("\n RECENT NEWS HEADLINES:")
    print("="*60)
    cursor.execute("""
        SELECT source, title, published
        FROM raw_data
        WHERE source_type = 'news'
        ORDER BY published DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  [{row['source']}] {row['title'][:60]}...")
    
    # 3. Sentiment breakdown
    print("\n SENTIMENT BREAKDOWN:")
    print("="*60)
    cursor.execute("""
        SELECT sentiment, COUNT(*) as count
        FROM social_posts
        GROUP BY sentiment
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row['sentiment']:20} {row['count']:4}")
    
    # 4. Locations mentioned
    print("\n TOP LOCATIONS:")
    print("="*60)
    cursor.execute("""
        SELECT location, COUNT(*) as count
        FROM social_posts
        GROUP BY location
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row['location']:20} {row['count']:4} mentions")

db.disconnect()