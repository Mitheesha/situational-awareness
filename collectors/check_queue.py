"""
Check Redis Queue - Show statistics and sample data
"""
import redis
import json
from collections import Counter

try:
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    r.ping()
    print("✅ Connected to Redis\n")
    
    queue_length = r.llen("collector:incoming")
    print(f"📊 Total messages in queue: {queue_length}\n")
    
    if queue_length > 0:
        print("="*70)
        print("📄 SAMPLE MESSAGES")
        print("="*70)
        
        sources = []
        source_types = []
        topics = []
        
        # Sample first 100 messages (or all if less)
        sample_size = min(100, queue_length)
        
        for i in range(sample_size):
            msg = r.lindex("collector:incoming", i)
            if msg:
                try:
                    data = json.loads(msg)
                    sources.append(data.get('source', 'Unknown'))
                    source_types.append(data.get('source_type', 'Unknown'))
                    
                    # Extract topics from social posts
                    if 'meta' in data and 'topic' in data['meta']:
                        topics.append(data['meta']['topic'])
                    
                    # Show first 5 messages
                    if i < 5:
                        print(f"\nMessage {i+1}:")
                        print(f"  Source: {data.get('source')}")
                        print(f"  Type: {data.get('source_type')}")
                        print(f"  Title: {data.get('title', '')[:80]}...")
                        
                        # Show topic if social post
                        if 'meta' in data and 'topic' in data['meta']:
                            print(f"  Topic: {data['meta']['topic']}")
                            print(f"  Urgency: {data['meta'].get('urgency', 'N/A')}")
                        
                        print(f"  Time: {data.get('published', 'N/A')[:19]}")
                        
                except json.JSONDecodeError:
                    continue
        
        # Statistics
        print("\n" + "="*70)
        print("📈 DATA STATISTICS")
        print("="*70)
        
        print("\n🗂️  Source Distribution:")
        source_counts = Counter(sources)
        for source, count in source_counts.most_common():
            bar = "█" * (count // 2)
            print(f"  {source:35} {count:3} {bar}")
        
        print("\n📊 Source Type Distribution:")
        type_counts = Counter(source_types)
        for stype, count in type_counts.most_common():
            percentage = (count / len(source_types)) * 100
            print(f"  {stype:20} {count:3} ({percentage:.1f}%)")
        
        if topics:
            print("\n🔥 Top Topics (from social posts):")
            topic_counts = Counter(topics)
            for topic, count in topic_counts.most_common(10):
                print(f"  {topic:30} {count:3}")
        
        print("\n" + "="*70)
        print("✅ System Status: OPERATIONAL")
        print("="*70)
        print(f"\n💡 Data Collection Rate:")
        print(f"   • {queue_length} total messages")
        print(f"   • {len(set(sources))} unique sources")
        print(f"   • Ready for pipeline processing\n")
        
    else:
        print("="*70)
        print("⚠️  QUEUE IS EMPTY")
        print("="*70)
        print("\n🔧 Start collectors to add data:")
        print("   • News: python collectors/news_scraper/run_scraper.py")
        print("   • Social: python collectors/social_listener/run_social.py\n")
        
except redis.ConnectionError:
    print("="*70)
    print("❌ CANNOT CONNECT TO REDIS")
    print("="*70)
    print("\n🚀 Start Redis with:")
    print("   cd infra")
    print("   docker compose up -d")
    print("   cd ..\n")
except Exception as e:
    print(f"❌ Error: {e}")