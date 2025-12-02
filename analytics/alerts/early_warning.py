"""
Early Warning System - Predictive Alerts
Generates warnings BEFORE situations become critical
INNOVATION: Forward-looking analysis using pattern + velocity
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import List, Dict
from analytics.models import Signal
from datetime import datetime, timedelta

class EarlyWarningSystem:
    """
    Generates early warnings based on pattern + velocity analysis
    
    Warnings are issued when:
    1. High velocity + high urgency = Threat accelerating
    2. Multiple correlated signals = Systemic risk
    3. Geographic concentration = Localized crisis
    4. Sustained high volume = Persistent problem
    """
    
    WARNING_TYPES = {
        'acceleration': {
            'icon': '🚨',
            'priority': 'CRITICAL',
            'description': 'Rapidly intensifying situation'
        },
        'correlation': {
            'icon': '⚠️',
            'priority': 'HIGH',
            'description': 'Multiple related indicators'
        },
        'geographic': {
            'icon': '📍',
            'priority': 'HIGH',
            'description': 'Localized concentration'
        },
        'persistence': {
            'icon': '🔔',
            'priority': 'MEDIUM',
            'description': 'Sustained high activity'
        },
        'cascade': {
            'icon': '🌊',
            'priority': 'CRITICAL',
            'description': 'Potential cascade effect'
        }
    }
    
    def generate_warnings(self, signals: List[Signal], velocities: Dict) -> List[Dict]:
        """
        Generate all early warnings
        
        Args:
            signals: Detected signals from pattern detector
            velocities: Topic velocity data
            
        Returns:
            List of warning dictionaries
        """
        warnings = []
        
        # Warning Type 1: Acceleration warnings
        warnings.extend(self._detect_acceleration_warnings(signals, velocities))
        
        # Warning Type 2: Correlation warnings
        warnings.extend(self._detect_correlation_warnings(signals))
        
        # Warning Type 3: Geographic warnings
        warnings.extend(self._detect_geographic_warnings(signals))
        
        # Warning Type 4: Persistence warnings
        warnings.extend(self._detect_persistence_warnings(signals))
        
        # Warning Type 5: Cascade warnings
        warnings.extend(self._detect_cascade_warnings(signals))
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        warnings.sort(key=lambda x: priority_order.get(x['priority'], 999))
        
        return warnings
    
    def _detect_acceleration_warnings(self, signals: List[Signal], velocities: Dict) -> List[Dict]:
        """Detect threats that are accelerating"""
        warnings = []
        
        for signal in signals:
            if signal.urgency not in ['critical', 'high']:
                continue
            
            if signal.topic in velocities:
                velocity_data = velocities[signal.topic]
                
                # High urgency + accelerating = WARNING
                if velocity_data['trend'] in ['ACCELERATING', 'GROWING']:
                    velocity_value = velocity_data['velocity']
                    
                    # Predict next 6 hours
                    current_rate = velocity_data['recent_avg']
                    predicted_rate = current_rate + (velocity_value * 6)
                    
                    warnings.append({
                        'type': 'acceleration',
                        'topic': signal.topic,
                        'priority': self.WARNING_TYPES['acceleration']['priority'],
                        'icon': self.WARNING_TYPES['acceleration']['icon'],
                        'title': f"Accelerating: {signal.topic.title()}",
                        'message': f"{signal.topic.title()} is rapidly intensifying (velocity: +{velocity_value:.1f}/hour)",
                        'prediction': f"If trend continues: ~{predicted_rate:.0f} mentions in 6 hours",
                        'confidence': min(95, signal.confidence_score + 10),
                        'recommended_action': f"Monitor {signal.topic} closely. Prepare response plans.",
                        'time_horizon': '6 hours',
                        'current_urgency': signal.urgency,
                        'metadata': {
                            'velocity': velocity_value,
                            'current_rate': current_rate,
                            'predicted_rate': predicted_rate
                        }
                    })
        
        return warnings
    
    def _detect_correlation_warnings(self, signals: List[Signal]) -> List[Dict]:
        """Detect multiple correlated signals (systemic risks)"""
        warnings = []
        
        # Economic correlation
        economic_topics = ['fuel prices', 'inflation', 'rupee exchange rate', 'economy', 'cost']
        economic_signals = [s for s in signals if any(t in s.topic.lower() for t in economic_topics)]
        
        if len(economic_signals) >= 2:
            topic_list = ', '.join(set(s.topic for s in economic_signals))
            avg_urgency = sum(1 if s.urgency in ['critical', 'high'] else 0 for s in economic_signals)
            
            warnings.append({
                'type': 'correlation',
                'topic': 'economic_cluster',
                'priority': 'HIGH' if avg_urgency >= 1 else 'MEDIUM',
                'icon': self.WARNING_TYPES['correlation']['icon'],
                'title': "Economic Pressure Indicators",
                'message': f"Multiple economic factors active: {topic_list}",
                'prediction': "Potential broader economic impact. Businesses should review financial resilience.",
                'confidence': 80,
                'recommended_action': "Review pricing strategy, cash reserves, and cost management plans.",
                'time_horizon': '1-2 weeks',
                'current_urgency': 'high',
                'metadata': {
                    'signal_count': len(economic_signals),
                    'topics': [s.topic for s in economic_signals]
                }
            })
        
        # Infrastructure correlation
        infra_topics = ['power cut', 'road conditions', 'transport', 'water shortage', 'electricity']
        infra_signals = [s for s in signals if any(t in s.topic.lower() for t in infra_topics)]
        
        if len(infra_signals) >= 2:
            topic_list = ', '.join(set(s.topic for s in infra_signals))
            
            warnings.append({
                'type': 'correlation',
                'topic': 'infrastructure_cluster',
                'priority': 'HIGH',
                'icon': self.WARNING_TYPES['correlation']['icon'],
                'title': "Infrastructure Stress Detected",
                'message': f"Multiple infrastructure issues: {topic_list}",
                'prediction': "Operational disruptions likely. Supply chains may be affected.",
                'confidence': 75,
                'recommended_action': "Activate business continuity plans. Prepare for service disruptions.",
                'time_horizon': '2-3 days',
                'current_urgency': 'high',
                'metadata': {
                    'signal_count': len(infra_signals),
                    'topics': [s.topic for s in infra_signals]
                }
            })
        
        return warnings
    
    def _detect_geographic_warnings(self, signals: List[Signal]) -> List[Dict]:
        """Detect geographic concentrations"""
        warnings = []
        
        # Count signals by location
        location_counts = {}
        for signal in signals:
            if 'location' in signal.metadata:
                location = signal.metadata['location']
                if location not in location_counts:
                    location_counts[location] = []
                location_counts[location].append(signal)
        
        # Check for hotspots
        for location, loc_signals in location_counts.items():
            if len(loc_signals) >= 3:  # 3+ signals in one location
                high_urgency = sum(1 for s in loc_signals if s.urgency in ['critical', 'high'])
                
                if high_urgency >= 2:
                    topics = ', '.join(set(s.topic for s in loc_signals[:3]))
                    
                    warnings.append({
                        'type': 'geographic',
                        'topic': f'{location}_hotspot',
                        'priority': 'HIGH',
                        'icon': self.WARNING_TYPES['geographic']['icon'],
                        'title': f"Hotspot Alert: {location}",
                        'message': f"Concentrated activity in {location}: {topics}",
                        'prediction': f"Localized disruptions likely in {location}. Consider alternative routes/locations.",
                        'confidence': 85,
                        'recommended_action': f"Avoid {location} if possible. Monitor local developments closely.",
                        'time_horizon': '12-24 hours',
                        'current_urgency': 'high',
                        'metadata': {
                            'location': location,
                            'signal_count': len(loc_signals),
                            'high_urgency_count': high_urgency
                        }
                    })
        
        return warnings
    
    def _detect_persistence_warnings(self, signals: List[Signal]) -> List[Dict]:
        """Detect sustained high-volume topics (not going away)"""
        warnings = []
        
        # Count mentions per topic
        topic_volumes = {}
        for signal in signals:
            topic = signal.topic
            if topic not in topic_volumes:
                topic_volumes[topic] = 0
            topic_volumes[topic] += signal.source_count
        
        # Check for sustained high volume
        for topic, volume in topic_volumes.items():
            if volume > 50:  # High volume threshold
                # Find matching signals
                topic_signals = [s for s in signals if s.topic == topic]
                
                if topic_signals:
                    max_urgency = max(s.urgency for s in topic_signals)
                    
                    warnings.append({
                        'type': 'persistence',
                        'topic': topic,
                        'priority': 'MEDIUM',
                        'icon': self.WARNING_TYPES['persistence']['icon'],
                        'title': f"Persistent Issue: {topic.title()}",
                        'message': f"{topic.title()} remains active with {volume} mentions",
                        'prediction': "Issue not resolving quickly. Plan for extended impact.",
                        'confidence': 70,
                        'recommended_action': f"Develop long-term mitigation strategy for {topic}.",
                        'time_horizon': '1 week+',
                        'current_urgency': max_urgency,
                        'metadata': {
                            'total_mentions': volume,
                            'signal_count': len(topic_signals)
                        }
                    })
        
        return warnings
    
    def _detect_cascade_warnings(self, signals: List[Signal]) -> List[Dict]:
        """Detect potential cascade effects (one problem causing others)"""
        warnings = []
        
        # Define cascade relationships
        cascade_chains = [
            {
                'trigger': ['fuel prices', 'rupee exchange rate'],
                'effects': ['inflation', 'cost', 'transport'],
                'title': 'Economic Cascade',
                'message': 'Fuel/currency issues may trigger broader inflation and transport costs'
            },
            {
                'trigger': ['flood warning', 'monsoon rain'],
                'effects': ['road conditions', 'power cut', 'water shortage'],
                'title': 'Weather Cascade',
                'message': 'Severe weather may cause infrastructure failures'
            },
            {
                'trigger': ['power cut'],
                'effects': ['water shortage', 'public transport'],
                'title': 'Infrastructure Cascade',
                'message': 'Power outages can disrupt water supply and transport systems'
            }
        ]
        
        for chain in cascade_chains:
            # Check if trigger exists
            trigger_signals = [
                s for s in signals 
                if any(t in s.topic.lower() for t in chain['trigger'])
            ]
            
            # Check if effects exist
            effect_signals = [
                s for s in signals 
                if any(e in s.topic.lower() for e in chain['effects'])
            ]
            
            # Cascade detected if both present
            if trigger_signals and effect_signals:
                trigger_topics = ', '.join(set(s.topic for s in trigger_signals))
                effect_topics = ', '.join(set(s.topic for s in effect_signals))
                
                warnings.append({
                    'type': 'cascade',
                    'topic': chain['title'].lower().replace(' ', '_'),
                    'priority': 'CRITICAL',
                    'icon': self.WARNING_TYPES['cascade']['icon'],
                    'title': chain['title'],
                    'message': chain['message'],
                    'prediction': f"Trigger: {trigger_topics} → Effects: {effect_topics}",
                    'confidence': 75,
                    'recommended_action': "Prepare for multi-system disruption. Review full business continuity plan.",
                    'time_horizon': '24-48 hours',
                    'current_urgency': 'critical',
                    'metadata': {
                        'triggers': [s.topic for s in trigger_signals],
                        'effects': [s.topic for s in effect_signals]
                    }
                })
        
        return warnings


def display_warnings(warnings: List[Dict]):
    """Pretty print early warnings"""
    if not warnings:
        print("\n✅ No early warnings generated - situation stable")
        return
    
    print("\n" + "="*70)
    print("🚨 EARLY WARNING SYSTEM - ALERTS")
    print("="*70)
    
    # Group by priority
    critical = [w for w in warnings if w['priority'] == 'CRITICAL']
    high = [w for w in warnings if w['priority'] == 'HIGH']
    medium = [w for w in warnings if w['priority'] == 'MEDIUM']
    
    if critical:
        print("\n🔴 CRITICAL WARNINGS:")
        print("-"*70)
        for warning in critical:
            print(f"\n{warning['icon']} {warning['title']}")
            print(f"   {warning['message']}")
            print(f"   Prediction: {warning['prediction']}")
            print(f"   Action: {warning['recommended_action']}")
            print(f"   Time Horizon: {warning['time_horizon']}")
            print(f"   Confidence: {warning['confidence']:.0f}%")
    
    if high:
        print("\n🟠 HIGH PRIORITY WARNINGS:")
        print("-"*70)
        for warning in high:
            print(f"\n{warning['icon']} {warning['title']}")
            print(f"   {warning['message']}")
            print(f"   Action: {warning['recommended_action']}")
    
    if medium:
        print("\n🟡 MEDIUM PRIORITY WARNINGS:")
        print("-"*70)
        for warning in medium:
            print(f"\n{warning['icon']} {warning['title']}")
            print(f"   {warning['message']}")


if __name__ == "__main__":
    from analytics.detectors.pattern_detector import PatternDetector
    from analytics.detectors.velocity_tracker import VelocityTracker
    
    print("🔍 Running pattern detection...")
    detector = PatternDetector()
    results = detector.run_all_detectors()
    detector.close()
    
    # Flatten signals
    all_signals = []
    for signals in results.values():
        all_signals.extend(signals)
    
    print("\n🚀 Calculating velocities...")
    tracker = VelocityTracker()
    velocities = tracker.calculate_topic_velocity()
    tracker.close()
    
    # Generate warnings
    print("\n⚠️  Generating early warnings...")
    ews = EarlyWarningSystem()
    warnings = ews.generate_warnings(all_signals, velocities)
    
    display_warnings(warnings)
    
    print("\n" + "="*70)
    print(f"📊 SUMMARY: {len(warnings)} warnings generated")
    print("="*70 + "\n")