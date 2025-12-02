"""
Analytics Summary - Quick overview of insights
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline.models.database import Database
from datetime import datetime

db = Database()
db.connect()

print("\n" + "="*70)
print("📊 ANALYTICS SUMMARY")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

with db.get_cursor(dict_cursor=True) as cursor:
    # Signals summary
    cursor.execute("SELECT COUNT(*), urgency FROM signals GROUP BY urgency")
    signals = cursor.fetchall()
    
    print("\n🔔 DETECTED SIGNALS:")
    for row in signals:
        print(f"   {row['urgency']:10} {row['count']:3}")
    
    # Insights summary
    cursor.execute("SELECT COUNT(*), severity FROM insights GROUP BY severity")
    insights = cursor.fetchall()
    
    print("\n💡 GENERATED INSIGHTS:")
    for row in insights:
        print(f"   {row['severity']:10} {row['count']:3}")
    
    # Recent insights
    print("\n📋 RECENT INSIGHTS:")
    cursor.execute("""
        SELECT title, severity, created_at 
        FROM insights 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   [{row['severity'].upper()}] {row['title']}")

db.disconnect()