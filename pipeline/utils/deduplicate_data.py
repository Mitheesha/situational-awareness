"""
Deduplicate Database Records
Keeps first occurrence, removes duplicates
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pipeline.models.database import Database

db = Database()
db.connect()

print("\n" + "="*70)
print("🧹 DEDUPLICATION IN PROGRESS")
print("="*70)

with db.get_cursor(dict_cursor=True) as cursor:
    # Get initial count
    cursor.execute("SELECT COUNT(*) as count FROM raw_data")
    initial_count = cursor.fetchone()['count']
    print(f"\n📊 Initial records: {initial_count:,}")
    
    # Count duplicates
    cursor.execute("""
        SELECT COUNT(*) as dup_count
        FROM (
            SELECT url, title, snippet, COUNT(*) as cnt
            FROM raw_data
            GROUP BY url, title, snippet
            HAVING COUNT(*) > 1
        ) duplicates
    """)
    duplicate_groups = cursor.fetchone()['dup_count']
    print(f"⚠️  Duplicate groups found: {duplicate_groups:,}")

print("\n🗑️  Removing duplicates (keeping earliest record)...")

with db.get_cursor() as cursor:
    # Delete duplicates, keeping only the first occurrence (lowest id)
    cursor.execute("""
        DELETE FROM raw_data
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM raw_data
            GROUP BY url, title, snippet
        )
    """)
    
    deleted_count = cursor.rowcount
    print(f"✅ Deleted {deleted_count:,} duplicate records")

# Verify
with db.get_cursor(dict_cursor=True) as cursor:
    cursor.execute("SELECT COUNT(*) as count FROM raw_data")
    final_count = cursor.fetchone()['count']
    print(f"📊 Final records: {final_count:,}")
    print(f"📉 Reduction: {initial_count - final_count:,} ({(initial_count - final_count)/initial_count*100:.1f}%)")

# Also clean up orphaned social posts
print("\n🧹 Cleaning orphaned social_posts...")
with db.get_cursor() as cursor:
    cursor.execute("""
        DELETE FROM social_posts
        WHERE raw_data_id NOT IN (SELECT id FROM raw_data)
    """)
    orphaned = cursor.rowcount
    print(f"✅ Removed {orphaned:,} orphaned social posts")

# Final statistics
print("\n" + "="*70)
print("✅ DEDUPLICATION COMPLETE")
print("="*70)

with db.get_cursor(dict_cursor=True) as cursor:
    cursor.execute("SELECT COUNT(*) FROM raw_data")
    total = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) FROM raw_data WHERE source_type = 'news'")
    news = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) FROM raw_data WHERE source_type = 'social'")
    social = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) FROM social_posts")
    social_posts = cursor.fetchone()['count']
    
    print(f"\n📊 Clean Database Statistics:")
    print(f"   Total Records: {total:,}")
    print(f"   News Articles: {news:,}")
    print(f"   Social Posts: {social:,}")
    print(f"   Social Metadata: {social_posts:,}")

print("\n" + "="*70 + "\n")

db.disconnect()