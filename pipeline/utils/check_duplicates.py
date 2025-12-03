"""
Check for duplicate data in database
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pipeline.models.database import Database

db = Database()
db.connect()

print("\n" + "="*70)
print("🔍 DUPLICATE DATA ANALYSIS")
print("="*70)

with db.get_cursor(dict_cursor=True) as cursor:
    # 1. Check URL duplicates
    print("\n📊 Checking URL duplicates...")
    cursor.execute("""
        SELECT url, COUNT(*) as count
        FROM raw_data
        WHERE url IS NOT NULL AND url != ''
        GROUP BY url
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """)
    url_dupes = cursor.fetchall()
    
    if url_dupes:
        print(f"   ⚠️  Found {len(url_dupes)} duplicate URLs:")
        for row in url_dupes:
            print(f"      {row['url'][:60]}... (appears {row['count']} times)")
    else:
        print("   ✅ No URL duplicates found!")
    
    # 2. Check title duplicates
    print("\n📊 Checking title duplicates...")
    cursor.execute("""
        SELECT title, COUNT(*) as count
        FROM raw_data
        GROUP BY title
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """)
    title_dupes = cursor.fetchall()
    
    if title_dupes:
        print(f"   ⚠️  Found {len(title_dupes)} duplicate titles:")
        for row in title_dupes:
            print(f"      '{row['title'][:60]}...' (appears {row['count']} times)")
    else:
        print("   ✅ No title duplicates found!")
    
    # 3. Check exact content duplicates
    print("\n📊 Checking exact content duplicates...")
    cursor.execute("""
        SELECT title, snippet, COUNT(*) as count
        FROM raw_data
        GROUP BY title, snippet
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """)
    content_dupes = cursor.fetchall()
    
    if content_dupes:
        print(f"   ⚠️  Found {len(content_dupes)} exact content duplicates:")
        for row in content_dupes:
            print(f"      '{row['title'][:60]}...' (appears {row['count']} times)")
    else:
        print("   ✅ No exact content duplicates found!")
    
    # 4. Overall statistics
    print("\n📈 Overall Statistics:")
    cursor.execute("SELECT COUNT(*) as total FROM raw_data")
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(DISTINCT url) as unique_urls FROM raw_data WHERE url IS NOT NULL")
    unique_urls = cursor.fetchone()['unique_urls']
    
    cursor.execute("SELECT COUNT(DISTINCT title) as unique_titles FROM raw_data")
    unique_titles = cursor.fetchone()['unique_titles']
    
    duplication_rate_urls = ((total - unique_urls) / total * 100) if total > 0 else 0
    duplication_rate_titles = ((total - unique_titles) / total * 100) if total > 0 else 0
    
    print(f"   Total Records: {total:,}")
    print(f"   Unique URLs: {unique_urls:,} (duplication: {duplication_rate_urls:.1f}%)")
    print(f"   Unique Titles: {unique_titles:,} (duplication: {duplication_rate_titles:.1f}%)")

print("\n" + "="*70 + "\n")

db.disconnect()