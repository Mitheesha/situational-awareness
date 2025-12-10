"""
Real-Time AI Sentiment Processor
Processes new data as it arrives with AI sentiment analysis
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
from datetime import datetime
from transformers import pipeline
from models.database import Database

class RealtimeAIProcessor:
    """Processes incoming data with AI sentiment analysis in real-time"""
    
    def __init__(self):
        self.db = Database()
        
        # Initialize AI model (loads once, reuses for all predictions)
        print("🤖 Loading AI sentiment model (DistilBERT)...")
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1  # CPU mode
        )
        print("AI model loaded successfully")
        
        self.stats = {
            'processed': 0,
            'start_time': datetime.now()
        }
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment using BERT model
        
        Returns:
            tuple: (label, score) e.g. ('POSITIVE', 0.95)
        """
        if not text or len(text.strip()) < 10:
            return 'NEUTRAL', 0.5
        
        try:
            # Truncate to 512 tokens (BERT limit)
            text = text[:512]
            result = self.sentiment_analyzer(text)[0]
            
            # Convert to numeric score (-1 to +1)
            label = result['label']
            confidence = result['score']
            
            if label == 'POSITIVE':
                sentiment_score = confidence
            else:  # NEGATIVE
                sentiment_score = -confidence
            
            return label, sentiment_score
            
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return 'NEUTRAL', 0.0
    
    def process_unprocessed_records(self):
        """Find and process records without AI sentiment"""
        
        if not self.db.connect():
            print("Cannot connect to database")
            return 0
        
        try:
            with self.db.get_cursor(dict_cursor=True) as cursor:
                # Find records without AI sentiment
                cursor.execute("""
                    SELECT id, title, snippet
                    FROM raw_data
                    WHERE metadata->>'ai_sentiment_score' IS NULL
                    ORDER BY created_at DESC
                    LIMIT 100
                """)
                
                records = cursor.fetchall()
                
                if not records:
                    return 0
                
                print(f"\nFound {len(records)} records to process")
                
                processed_count = 0
                
                for record in records:
                    try:
                        # Combine title and snippet for analysis
                        text = f"{record['title']} {record['snippet']}"
                        
                        # Get AI sentiment
                        label, score = self.analyze_sentiment(text)
                        
                        # Update database
                        cursor.execute("""
                            UPDATE raw_data
                            SET metadata = COALESCE(metadata, '{}'::jsonb) || 
                                jsonb_build_object(
                                    'ai_sentiment_label', %s,
                                    'ai_sentiment_score', %s,
                                    'ai_processed_at', %s
                                )
                            WHERE id = %s
                        """, (label, float(score), datetime.now().isoformat(), record['id']))
                        
                        processed_count += 1
                        self.stats['processed'] += 1
                        
                        # Progress indicator
                        if processed_count % 10 == 0:
                            print(f"Processed {processed_count}/{len(records)} records...")
                        
                    except Exception as e:
                        print(f"Error processing record {record['id']}: {e}")
                        continue
                
                print(f"\nBatch complete: {processed_count} records processed")
                return processed_count
                
        except Exception as e:
            print(f"Processing error: {e}")
            return 0
        
        finally:
            self.db.disconnect()
    
    def run_continuous(self, check_interval=30):
        """
        Run processor continuously
        
        Args:
            check_interval: Seconds between checks for new data
        """
        print("="*70)
        print("REAL-TIME AI PROCESSOR STARTED")
        print("="*70)
        print(f"Model: DistilBERT (Sentiment Analysis)")
        print(f"Check interval: {check_interval} seconds")
        print(f"Processing: New records without AI sentiment")
        print("="*70)
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                processed = self.process_unprocessed_records()
                
                if processed > 0:
                    runtime = (datetime.now() - self.stats['start_time']).total_seconds()
                    rate = self.stats['processed'] / runtime if runtime > 0 else 0
                    print(f"Total processed: {self.stats['processed']} | Rate: {rate:.2f} records/sec")
                else:
                    print(f"No new records (checked at {datetime.now().strftime('%H:%M:%S')})")
                
                print(f"Waiting {check_interval} seconds...\n")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.print_final_stats()
    
    def print_final_stats(self):
        """Print final statistics"""
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        print("\n\n" + "="*70)
        print("AI PROCESSOR SHUTTING DOWN")
        print("="*70)
        print(f"  Total Records Processed: {self.stats['processed']}")
        print(f"  Runtime: {runtime:.0f} seconds")
        print(f"  Average Rate: {self.stats['processed']/runtime:.2f} records/sec")
        print("="*70 + "\n")


if __name__ == "__main__":
    processor = RealtimeAIProcessor()
    processor.run_continuous(check_interval=30)