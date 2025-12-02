"""
Velocity Tracker - Detect Acceleration & Deceleration
Measures how fast topics are changing (rate of change)
INNOVATION: Time-derivative analysis for early trend detection
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
from typing import Dict, List
from pipeline.models.database import Database
import statistics

class VelocityTracker:
    """
    Tracks velocity (rate of change) of topic mentions
    Helps identify accelerating threats vs declining concerns
    """
    
    def __init__(self):
        self.db = Database()
        self.db.connect()
    
    def calculate_topic_velocity(self, hours_window=12) -> Dict:
        """
        Calculate velocity for all topics
        
        Velocity = rate of change in mentions per hour
        Positive velocity = accelerating (growing concern)
        Negative velocity = decelerating (declining concern)
        
        Args:
            hours_window: Hours to analyze
            
        Returns:
            Dictionary of topic velocities with metadata
        """
        with self.db.get_cursor(dict_cursor=True) as cursor:
            # Get hourly mention counts
            cursor.execute("""
                SELECT 
                    topic,
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as count
                FROM social_posts
                WHERE created_at > NOW() - INTERVAL '%s hours'
                GROUP BY topic, DATE_TRUNC('hour', created_at)
                ORDER BY topic, hour
            """, (hours_window * 2,))  # Get double window for comparison
            
            data = cursor.fetchall()
        
        if not data:
            return {}
        
        # Group by topic
        topics = {}
        for row in data:
            topic = row['topic']
            if topic not in topics:
                topics[topic] = {
                    'hourly_counts': [],
                    'timestamps': []
                }
            topics[topic]['hourly_counts'].append(row['count'])
            topics[topic]['timestamps'].append(row['hour'])
        
        # Calculate velocity for each topic
        velocities = {}
        
        for topic, topic_data in topics.items():
            counts = topic_data['hourly_counts']
            
            if len(counts) < 3:
                continue  # Need minimum data points
            
            # Split into recent vs older periods
            split_point = len(counts) // 2
            older_counts = counts[:split_point]
            recent_counts = counts[split_point:]
            
            if not older_counts or not recent_counts:
                continue
            
            # Calculate averages
            older_avg = statistics.mean(older_counts)
            recent_avg = statistics.mean(recent_counts)
            
            # Velocity = change per hour
            time_span = len(counts)
            velocity = (recent_avg - older_avg) / (time_span / 2) if time_span > 0 else 0
            
            # Acceleration classification
            if velocity > 2:
                trend = "ACCELERATING"
                urgency = "high"
                description = f"Rapidly increasing (↑{velocity:.1f} mentions/hour)"
            elif velocity > 0.5:
                trend = "GROWING"
                urgency = "medium"
                description = f"Steadily growing (↑{velocity:.1f} mentions/hour)"
            elif velocity > -0.5:
                trend = "STABLE"
                urgency = "low"
                description = f"Relatively stable (~{velocity:.1f} mentions/hour)"
            elif velocity > -2:
                trend = "DECLINING"
                urgency = "low"
                description = f"Gradually declining (↓{abs(velocity):.1f} mentions/hour)"
            else:
                trend = "FADING"
                urgency = "low"
                description = f"Rapidly fading (↓{abs(velocity):.1f} mentions/hour)"
            
            # Calculate momentum (current trajectory)
            if len(recent_counts) >= 2:
                momentum = recent_counts[-1] - recent_counts[-2]
            else:
                momentum = 0
            
            velocities[topic] = {
                'velocity': round(velocity, 2),
                'trend': trend,
                'urgency': urgency,
                'description': description,
                'recent_avg': round(recent_avg, 1),
                'older_avg': round(older_avg, 1),
                'momentum': momentum,
                'data_points': len(counts),
                'latest_count': counts[-1]
            }
        
        return velocities
    
    def get_accelerating_topics(self, velocities: Dict, min_velocity: float = 1.0) -> List[Dict]:
        """
        Get topics that are accelerating above threshold
        
        These are early warning indicators!
        """
        accelerating = []
        
        for topic, data in velocities.items():
            if data['velocity'] > min_velocity:
                accelerating.append({
                    'topic': topic,
                    'velocity': data['velocity'],
                    'trend': data['trend'],
                    'recent_avg': data['recent_avg'],
                    'warning': f"⚠️  {topic} is accelerating at {data['velocity']:.1f} mentions/hour"
                })
        
        # Sort by velocity (fastest first)
        return sorted(accelerating, key=lambda x: x['velocity'], reverse=True)
    
    def get_decelerating_topics(self, velocities: Dict, max_velocity: float = -1.0) -> List[Dict]:
        """
        Get topics that are fading
        
        Good news - problems are resolving!
        """
        decelerating = []
        
        for topic, data in velocities.items():
            if data['velocity'] < max_velocity:
                decelerating.append({
                    'topic': topic,
                    'velocity': data['velocity'],
                    'trend': data['trend'],
                    'recent_avg': data['recent_avg'],
                    'info': f"✅ {topic} is declining at {abs(data['velocity']):.1f} mentions/hour"
                })
        
        return sorted(decelerating, key=lambda x: x['velocity'])
    
    def close(self):
        self.db.disconnect()


def display_velocities(velocities: Dict):
    """Pretty print velocity analysis"""
    print("\n" + "="*70)
    print("🚀 TOPIC VELOCITY ANALYSIS")
    print("="*70)
    print("Velocity = Rate of change (mentions per hour)")
    print("Positive = Accelerating | Negative = Decelerating")
    print("-"*70)
    
    # Sort by absolute velocity (most change first)
    sorted_topics = sorted(
        velocities.items(), 
        key=lambda x: abs(x[1]['velocity']), 
        reverse=True
    )
    
    for topic, data in sorted_topics[:15]:  # Top 15
        # Icon based on trend
        if data['trend'] == 'ACCELERATING':
            icon = "🔴📈"
        elif data['trend'] == 'GROWING':
            icon = "🟡📈"
        elif data['trend'] == 'STABLE':
            icon = "🟢➡️"
        elif data['trend'] == 'DECLINING':
            icon = "🟢📉"
        else:
            icon = "⚪📉"
        
        velocity_str = f"+{data['velocity']:.2f}" if data['velocity'] >= 0 else f"{data['velocity']:.2f}"
        
        print(f"\n{icon} {topic}")
        print(f"   Velocity: {velocity_str} mentions/hour | Trend: {data['trend']}")
        print(f"   Recent avg: {data['recent_avg']:.1f} | Previous avg: {data['older_avg']:.1f}")
        print(f"   {data['description']}")


if __name__ == "__main__":
    tracker = VelocityTracker()
    
    print("\n🔍 Calculating topic velocities...")
    velocities = tracker.calculate_topic_velocity(hours_window=12)
    
    if not velocities:
        print("❌ Not enough data for velocity analysis")
        tracker.close()
        exit()
    
    # Display all velocities
    display_velocities(velocities)
    
    # Highlight accelerating topics
    print("\n" + "="*70)
    print("🚨 ACCELERATING TOPICS (Early Warnings)")
    print("="*70)
    
    accelerating = tracker.get_accelerating_topics(velocities, min_velocity=0.5)
    
    if accelerating:
        for item in accelerating[:5]:
            print(f"\n{item['warning']}")
            print(f"   Current rate: {item['recent_avg']:.1f} mentions/hour")
    else:
        print("\n✅ No rapidly accelerating topics detected")
    
    # Show declining topics
    print("\n" + "="*70)
    print("✅ DECLINING TOPICS (Concerns Fading)")
    print("="*70)
    
    decelerating = tracker.get_decelerating_topics(velocities, max_velocity=-0.5)
    
    if decelerating:
        for item in decelerating[:5]:
            print(f"\n{item['info']}")
            print(f"   Current rate: {item['recent_avg']:.1f} mentions/hour")
    else:
        print("\n⚠️  No topics showing significant decline")
    
    print("\n" + "="*70 + "\n")
    
    tracker.close()