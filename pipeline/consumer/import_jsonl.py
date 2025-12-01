"""
Import JSONL dump file to PostgreSQL
Batch processing with progress tracking
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import json
import time
from datetime import datetime
from pipeline.models.database import Database

def import_jsonl(filename, batch_size=50):
    """
    Import JSONL file to database with batch processing
    
    Args:
        filename: Path to JSONL file
        batch_size: Number of records to commit at once
    """
    db = Database()
    
    if not db.connect():
        print("❌ Cannot connect to database")
        print("   Make sure Docker is running: docker compose up -d")
        return
    
    print(f"\n{'='*70}")
    print(f"📂 Importing: {filename}")
    print(f"{'='*70}\n")
    
    imported = 0
    errors = 0
    start_time = time.time()
    
    source_breakdown = {}
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total_lines = len(lines)
            
            print(f"📊 Total records to import: {total_lines}\n")
            
            for line_num, line in enumerate(lines, 1):
                try:
                    data = json.loads(line.strip())
                    
                    # Insert record
                    record_id = db.insert_raw_data(data)
                    
                    if record_id:
                        imported += 1
                        
                        # Track by source
                        source = data.get('source', 'Unknown')
                        source_breakdown[source] = source_breakdown.get(source, 0) + 1
                        
                        # Progress indicator
                        if imported % batch_size == 0:
                            progress = (line_num / total_lines) * 100
                            elapsed = time.time() - start_time
                            rate = imported / elapsed if elapsed > 0 else 0
                            
                            print(f"⏳ Progress: {progress:.1f}% | "
                                  f"Imported: {imported} | "
                                  f"Rate: {rate:.1f} records/sec")
                    else:
                        errors += 1
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Line {line_num}: Invalid JSON - {e}")
                    errors += 1
                except Exception as e:
                    print(f"❌ Line {line_num}: Error - {e}")
                    errors += 1
        
        # Final statistics
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"✅ IMPORT COMPLETE!")
        print(f"{'='*70}")
        print(f"  Records Imported: {imported}")
        print(f"  Errors: {errors}")
        print(f"  Time Taken: {elapsed_time:.2f} seconds")
        print(f"  Average Rate: {imported/elapsed_time:.2f} records/sec")
        print(f"{'='*70}\n")
        
        # Source breakdown
        print("📊 Import Breakdown by Source:")
        for source, count in sorted(source_breakdown.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * (count // 20)
            print(f"  {source:35} {count:4} {bar}")
        
        # Database stats
        print(f"\n{'='*70}")
        print("📊 DATABASE STATUS:")
        print(f"{'='*70}")
        stats = db.get_statistics()
        print(f"  Total Records: {stats.get('total_records', 0)}")
        print(f"  News Articles: {stats.get('by_type', {}).get('news', 0)}")
        print(f"  Social Posts: {stats.get('by_type', {}).get('social', 0)}")
        print(f"  Last 24 Hours: {stats.get('last_24h', 0)}")
        
        if stats.get('top_topics'):
            print(f"\n  Top Social Topics:")
            for topic, count in stats['top_topics'].items():
                print(f"    • {topic}: {count} mentions")
        
        print(f"{'='*70}\n")
        
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        db.disconnect()


if __name__ == "__main__":
    import_file = Path("data_output/export/redis_dump.jsonl")
    
    if import_file.exists():
        print("\n🚀 Starting import from JSONL dump...\n")
        import_jsonl(import_file, batch_size=50)
    else:
        print(f"\n❌ Dump file not found: {import_file}")
        print("\n💡 Expected location: data_output/export/redis_dump.jsonl")
        print("   Did you run dump_all.py to export from Redis?")