"""
Redis Queue Consumer - Continuous Processing
Reads from Redis and stores in PostgreSQL
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import redis
import json
import time
from datetime import datetime

from pipeline.models.database import Database

class RedisConsumer:
    """Consumes messages from Redis queue and stores in database"""
    
    def __init__(self):
        self.redis_client = None
        self.db = Database()
        self.stats = {
            'processed': 0,
            'errors': 0,
            'by_source': {},
            'start_time': datetime.now()
        }
    
    def connect_redis(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            print("✅ Connected to Redis")
            return True
        except redis.ConnectionError:
            print("❌ Cannot connect to Redis")
            print("   Start with: cd infra && docker compose up -d")
            return False
    
    def process_message(self, message):
        """Process a single message"""
        try:
            data = json.loads(message)
            
            # Insert into database
            record_id = self.db.insert_raw_data(data)
            
            if record_id:
                self.stats['processed'] += 1
                
                # Track by source
                source = data.get('source', 'Unknown')
                self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + 1
                
                return True
            else:
                self.stats['errors'] += 1
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            self.stats['errors'] += 1
            return False
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            self.stats['errors'] += 1
            return False
    
    def consume_batch(self, batch_size=10):
        """Consume a batch of messages from Redis"""
        processed_count = 0
        
        for _ in range(batch_size):
            # Pop message from queue
            message = self.redis_client.lpop('collector:incoming')
            
            if message:
                if self.process_message(message):
                    processed_count += 1
            else:
                break  # Queue is empty
        
        return processed_count
    
    def run_continuous(self, batch_size=10, interval=5):
        """
        Run consumer continuously
        
        Args:
            batch_size: Number of messages to process per cycle
            interval: Seconds to wait between cycles
        """
        print("="*70)
        print("🔄 REDIS CONSUMER - LAYER 2 PIPELINE")
        print("="*70)
        print(f"⚙️  Batch size: {batch_size}")
        print(f"⏱️  Check interval: {interval} seconds")
        print(f"📤 Source: Redis queue 'collector:incoming'")
        print(f"📥 Destination: PostgreSQL database")
        print("="*70)
        print("💡 Press Ctrl+C to stop\n")
        
        try:
            while True:
                queue_length = self.redis_client.llen('collector:incoming')
                
                if queue_length > 0:
                    print(f"\n📥 Queue: {queue_length} messages waiting")
                    processed = self.consume_batch(batch_size)
                    
                    if processed > 0:
                        print(f"✅ Processed {processed} messages | Total: {self.stats['processed']}")
                        
                        # Show stats periodically
                        if self.stats['processed'] % 50 == 0:
                            self.print_stats()
                else:
                    current_time = datetime.now().strftime('%H:%M:%S')
                    print(f"⏳ Queue empty (checked at {current_time}) | Total processed: {self.stats['processed']}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.print_final_stats()
    
    def print_stats(self):
        """Print current statistics"""
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()
        rate = self.stats['processed'] / runtime if runtime > 0 else 0
        
        print("\n" + "="*70)
        print("📊 PROCESSING STATISTICS")
        print("="*70)
        print(f"  Total Processed: {self.stats['processed']}")
        print(f"  Errors: {self.stats['errors']}")
        print(f"  Processing Rate: {rate:.2f} messages/sec")
        print(f"  Runtime: {runtime:.0f} seconds")
        
        if self.stats['by_source']:
            print("\n  By Source:")
            for source, count in sorted(self.stats['by_source'].items(), key=lambda x: x[1], reverse=True):
                print(f"    {source}: {count}")
        
        print("="*70 + "\n")
    
    def print_final_stats(self):
        """Print final statistics before shutdown"""
        print("\n\n" + "="*70)
        print("👋 CONSUMER SHUTTING DOWN")
        print("="*70)
        self.print_stats()
        
        # Show database stats
        db_stats = self.db.get_statistics()
        print("📊 DATABASE STATUS:")
        print(f"  Total Records: {db_stats.get('total_records', 0)}")
        print(f"  News Articles: {db_stats.get('by_type', {}).get('news', 0)}")
        print(f"  Social Posts: {db_stats.get('by_type', {}).get('social', 0)}")
        print(f"  Last 24 Hours: {db_stats.get('last_24h', 0)}")
        print("="*70 + "\n")
    
    def start(self):
        """Initialize and start consumer"""
        # Connect to Redis
        if not self.connect_redis():
            return
        
        # Connect to Database
        if not self.db.connect():
            print("❌ Failed to connect to database")
            print("   Make sure Docker is running: docker compose up -d")
            return
        
        # Start consuming
        self.run_continuous()


if __name__ == "__main__":
    consumer = RedisConsumer()
    consumer.start()