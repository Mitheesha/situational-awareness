"""
Pattern Detection - Identifies spikes, trends, and anomalies
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
from collections import Counter
from typing import List, Dict, Tuple
from pipeline.models.database import Database
from analytics.models import Signal
import statistics

class PatternDetector:
    """Detects patterns and anomalies in collected data"""
    
    def __init__(self):
        self.db = Database()
        self.db.connect()
    
    def detect_topic_spikes(self, threshold_multiplier=2.0) -> List[Signal]:
        """
        Detect topics with unusually high mention volume
        
        Args:
            threshold_multiplier: How many times above average = spike
            
        Returns:
            List of spike signals
        """
        signals = []
        
        with self.db.get_cursor(dict_cursor=True) as cursor:
            # Get topic counts
            cursor.execute("""
                SELECT topic, COUNT(*) as count, urgency
                FROM social_posts
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY topic, urgency
            """)
            
            topic_data = cursor.fetchall()
            
            if not topic_data:
                return signals
            
            # Calculate baseline (average mentions per topic)
            counts = [row['count'] for row in topic_data]
            avg_count = statistics.mean(counts)
            std_dev = statistics.stdev(counts) if len(counts) > 1 else 0
            
            # Detect spikes
            for row in topic_data:
                if row['count'] > avg_count * threshold_multiplier:
                    # This is a spike!
                    severity_multiplier = row['count'] / avg_count
                    
                    signal = Signal(
                        signal_id=f"spike_{row['topic']}_{datetime.now().timestamp()}",
                        signal_type='spike',
                        topic=row['topic'],
                        description=f"Spike detected: {row['topic']} mentioned {row['count']} times ({severity_multiplier:.1f}x baseline)",
                        urgency=self._calculate_spike_urgency(row['count'], avg_count, row['urgency']),
                        confidence_score=min(95, 70 + (severity_multiplier * 5)),
                        source_count=row['count'],
                        first_seen=datetime.now() - timedelta(hours=24),
                        last_seen=datetime.now(),
                        metadata={
                            'baseline_avg': avg_count,
                            'actual_count': row['count'],
                            'multiplier': severity_multiplier,
                            'inherent_urgency': row['urgency']
                        }
                    )
                    signals.append(signal)
        
        return signals
    
    def detect_trending_topics(self, hours=24) -> List[Signal]:
        """
        Detect topics with increasing momentum
        """
        signals = []
        
        with self.db.get_cursor(dict_cursor=True) as cursor:
            # Get hourly topic counts
            cursor.execute("""
                SELECT 
                    topic,
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as count
                FROM social_posts
                WHERE created_at > NOW() - INTERVAL '%s hours'
                GROUP BY topic, DATE_TRUNC('hour', created_at)
                ORDER BY topic, hour
            """, (hours,))
            
            data = cursor.fetchall()
            
            # Group by topic
            topics = {}
            for row in data:
                if row['topic'] not in topics:
                    topics[row['topic']] = []
                topics[row['topic']].append(row['count'])
            
            # Detect upward trends
            for topic, counts in topics.items():
                if len(counts) < 3:
                    continue
                
                # Calculate trend (simple: compare recent vs older)
                recent_avg = statistics.mean(counts[-3:])
                older_avg = statistics.mean(counts[:-3]) if len(counts) > 3 else counts[0]
                
                if recent_avg > older_avg * 1.5:  # 50% increase
                    velocity = (recent_avg - older_avg) / len(counts)
                    
                    signal = Signal(
                        signal_id=f"trend_{topic}_{datetime.now().timestamp()}",
                        signal_type='trend',
                        topic=topic,
                        description=f"Upward trend: {topic} mentions increasing (recent: {recent_avg:.1f}, baseline: {older_avg:.1f})",
                        urgency='medium',
                        confidence_score=75,
                        source_count=sum(counts),
                        first_seen=datetime.now() - timedelta(hours=hours),
                        last_seen=datetime.now(),
                        metadata={
                            'velocity': velocity,
                            'recent_avg': recent_avg,
                            'older_avg': older_avg,
                            'hourly_counts': counts
                        }
                    )
                    signals.append(signal)
        
        return signals
    
    def detect_geographic_hotspots(self, min_mentions=30) -> List[Signal]:
        """
        Detect locations with concentrated activity
        """
        signals = []
        
        with self.db.get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                SELECT 
                    location,
                    urgency,
                    COUNT(*) as count,
                    STRING_AGG(DISTINCT topic, ', ') as topics
                FROM social_posts
                WHERE created_at > NOW() - INTERVAL '24 hours'
                  AND urgency IN ('high', 'medium')
                GROUP BY location, urgency
                HAVING COUNT(*) > %s
                ORDER BY count DESC
            """, (min_mentions,))
            
            for row in cursor.fetchall():
                signal = Signal(
                    signal_id=f"hotspot_{row['location']}_{datetime.now().timestamp()}",
                    signal_type='geographic_hotspot',
                    topic=f"Activity in {row['location']}",
                    description=f"High activity detected in {row['location']}: {row['count']} {row['urgency']}-urgency posts",
                    urgency=row['urgency'],
                    confidence_score=85,
                    source_count=row['count'],
                    first_seen=datetime.now() - timedelta(hours=24),
                    last_seen=datetime.now(),
                    metadata={
                        'location': row['location'],
                        'topics': row['topics'],
                        'urgency_level': row['urgency']
                    }
                )
                signals.append(signal)
        
        return signals
    
    def detect_sentiment_shifts(self) -> List[Signal]:
        """
        Detect significant sentiment changes
        """
        signals = []
        
        with self.db.get_cursor(dict_cursor=True) as cursor:
            # Get sentiment distribution by topic
            cursor.execute("""
                SELECT 
                    topic,
                    sentiment,
                    COUNT(*) as count
                FROM social_posts
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY topic, sentiment
            """)
            
            data = cursor.fetchall()
            
            # Group by topic
            topic_sentiments = {}
            for row in data:
                if row['topic'] not in topic_sentiments:
                    topic_sentiments[row['topic']] = {}
                topic_sentiments[row['topic']][row['sentiment']] = row['count']
            
            # Detect negative-heavy topics
            for topic, sentiments in topic_sentiments.items():
                total = sum(sentiments.values())
                negative_count = sentiments.get('negative', 0) + sentiments.get('frustration', 0) + sentiments.get('concern', 0)
                negative_pct = (negative_count / total) * 100 if total > 0 else 0
                
                if negative_pct > 60 and total > 20:  # >60% negative with significant volume
                    signal = Signal(
                        signal_id=f"sentiment_{topic}_{datetime.now().timestamp()}",
                        signal_type='sentiment_shift',
                        topic=topic,
                        description=f"Negative sentiment detected: {topic} ({negative_pct:.0f}% negative out of {total} mentions)",
                        urgency='medium' if negative_pct < 75 else 'high',
                        confidence_score=80,
                        source_count=total,
                        first_seen=datetime.now() - timedelta(hours=24),
                        last_seen=datetime.now(),
                        metadata={
                            'sentiment_breakdown': sentiments,
                            'negative_percentage': negative_pct
                        }
                    )
                    signals.append(signal)
        
        return signals
    
    def _calculate_spike_urgency(self, count, avg, inherent_urgency):
        """Calculate urgency level for a spike"""
        multiplier = count / avg if avg > 0 else 1
        
        if multiplier > 3 or inherent_urgency == 'high':
            return 'critical'
        elif multiplier > 2.5:
            return 'high'
        elif multiplier > 2:
            return 'medium'
        else:
            return 'low'
    
    def run_all_detectors(self) -> Dict[str, List[Signal]]:
        """Run all pattern detectors and return results"""
        print("\n" + "="*70)
        print("🔍 RUNNING PATTERN DETECTION")
        print("="*70)
        
        results = {}
        
        print("\n📊 Detecting topic spikes...")
        results['spikes'] = self.detect_topic_spikes()
        print(f"   Found {len(results['spikes'])} spike signals")
        
        print("\n📈 Detecting trending topics...")
        results['trends'] = self.detect_trending_topics()
        print(f"   Found {len(results['trends'])} trend signals")
        
        print("\n📍 Detecting geographic hotspots...")
        results['hotspots'] = self.detect_geographic_hotspots()
        print(f"   Found {len(results['hotspots'])} hotspot signals")
        
        print("\n😔 Detecting sentiment shifts...")
        results['sentiment_shifts'] = self.detect_sentiment_shifts()
        print(f"   Found {len(results['sentiment_shifts'])} sentiment signals")
        
        total_signals = sum(len(v) for v in results.values())
        print(f"\n✅ Total signals detected: {total_signals}")
        print("="*70 + "\n")
        
        return results
    
    def close(self):
        self.db.disconnect()

if __name__ == "__main__":
    detector = PatternDetector()
    
    results = detector.run_all_detectors()
    
    # Display results
    print("\n🚨 CRITICAL SIGNALS:")
    print("="*70)
    for category, signals in results.items():
        for signal in signals:
            if signal.urgency in ['critical', 'high']:
                print(f"\n{signal.signal_type.upper()}: {signal.topic}")
                print(f"  {signal.description}")
                print(f"  Urgency: {signal.urgency} | Confidence: {signal.confidence_score:.0f}%")
    
    detector.close()