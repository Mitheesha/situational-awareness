"""
Database connection and operations for Layer 2
"""
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from contextlib import contextmanager
from datetime import datetime
import json

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'modelx',
    'user': 'modelxuser',
    'password': 'modelxpass'
}

class Database:
    """Database connection and operations manager"""
    
    def __init__(self, config=None):
        self.config = config or DB_CONFIG
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.config)
            print("✅ Connected to PostgreSQL")
            return True
        except psycopg2.Error as e:
            print(f"❌ Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("👋 Disconnected from PostgreSQL")
    
    @contextmanager
    def get_cursor(self, dict_cursor=False):
        """Context manager for database cursor"""
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = self.connection.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def insert_raw_data(self, data):
        """
        Insert collected data into raw_data table
        
        Args:
            data: Dictionary with collected data
            
        Returns:
            record_id or None if failed
        """
        try:
            with self.get_cursor() as cursor:
                # Parse timestamps safely
                published = data.get('published')
                fetched_at = data.get('fetched_at') or datetime.utcnow().isoformat()
                
                # Prepare metadata (exclude meta for social posts, we'll extract that)
                metadata = {}
                if data.get('source_type') == 'news':
                    metadata = {
                        'raw_snippet': data.get('snippet', '')[:500]
                    }
                
                cursor.execute("""
                    INSERT INTO raw_data 
                    (source, source_type, url, title, snippet, published, 
                     fetched_at, language, collector, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data.get('source'),
                    data.get('source_type'),
                    data.get('url'),
                    data.get('title'),
                    data.get('snippet', '')[:2000],  # Limit length
                    published,
                    fetched_at,
                    data.get('language'),
                    data.get('collector'),
                    Json(metadata)
                ))
                
                record_id = cursor.fetchone()[0]
                
                # If social post, extract metadata to social_posts table
                if data.get('source_type') == 'social' and 'meta' in data:
                    self._insert_social_metadata(cursor, record_id, data['meta'])
                
                return record_id
                
        except Exception as e:
            print(f"❌ Error inserting data: {e}")
            return None
    
    def _insert_social_metadata(self, cursor, raw_data_id, meta):
        """Extract and insert social post metadata"""
        try:
            cursor.execute("""
                INSERT INTO social_posts 
                (raw_data_id, topic, sentiment, urgency, location, 
                 username, user_followers, retweet_count, like_count, is_simulated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                raw_data_id,
                meta.get('topic'),
                meta.get('sentiment'),
                meta.get('urgency'),
                meta.get('location'),
                meta.get('username'),
                meta.get('user_followers'),
                meta.get('retweet_count'),
                meta.get('like_count'),
                meta.get('simulated', False)
            ))
        except Exception as e:
            print(f"⚠️  Warning: Could not insert social metadata: {e}")
    
    def get_recent_data(self, limit=10):
        """Get recent collected data"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT id, source, source_type, title, published, fetched_at
                    FROM raw_data
                    ORDER BY fetched_at DESC
                    LIMIT %s
                """, (limit,))
                
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return []
    
    def get_statistics(self):
        """Get comprehensive database statistics"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                stats = {}
                
                # Total records
                cursor.execute("SELECT COUNT(*) as count FROM raw_data")
                stats['total_records'] = cursor.fetchone()['count']
                
                # By source
                cursor.execute("""
                    SELECT source, COUNT(*) as count
                    FROM raw_data 
                    GROUP BY source 
                    ORDER BY count DESC
                """)
                stats['by_source'] = {row['source']: row['count'] for row in cursor.fetchall()}
                
                # By type
                cursor.execute("""
                    SELECT source_type, COUNT(*) as count
                    FROM raw_data 
                    GROUP BY source_type
                """)
                stats['by_type'] = {row['source_type']: row['count'] for row in cursor.fetchall()}
                
                # Recent 24 hours
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM raw_data 
                    WHERE fetched_at > NOW() - INTERVAL '24 hours'
                """)
                stats['last_24h'] = cursor.fetchone()['count']
                
                # Social post stats
                cursor.execute("SELECT COUNT(*) as count FROM social_posts")
                stats['social_posts'] = cursor.fetchone()['count']
                
                # Top topics (if any social posts)
                if stats['social_posts'] > 0:
                    cursor.execute("""
                        SELECT topic, COUNT(*) as count
                        FROM social_posts
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                        GROUP BY topic
                        ORDER BY count DESC
                        LIMIT 5
                    """)
                    stats['top_topics'] = {row['topic']: row['count'] for row in cursor.fetchall()}
                
                return stats
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {}
    
    def get_hourly_collection_rate(self):
        """Get hourly collection statistics"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT * FROM hourly_collection_rate
                    LIMIT 24
                """)
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error: {e}")
            return []


if __name__ == "__main__":
    # Test database connection
    db = Database()
    if db.connect():
        print("\n📊 Database Statistics:")
        stats = db.get_statistics()
        print(f"  Total Records: {stats.get('total_records', 0)}")
        print(f"  Last 24 Hours: {stats.get('last_24h', 0)}")
        print(f"  Social Posts: {stats.get('social_posts', 0)}")
        
        if stats.get('by_source'):
            print("\n  By Source:")
            for source, count in stats['by_source'].items():
                print(f"    {source}: {count}")
        
        if stats.get('top_topics'):
            print("\n  Top Topics:")
            for topic, count in stats['top_topics'].items():
                print(f"    {topic}: {count}")
        
        db.disconnect()