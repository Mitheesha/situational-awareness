"""
Insight Generator - Converts signals into business insights
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
from typing import List, Dict
from analytics.models import Signal, Insight
from collections import Counter
import uuid

class InsightGenerator:
    """Generates actionable business insights from signals"""
    
    def __init__(self):
        self.insight_templates = {
            'operational_risk': {
                'fuel prices': "Monitor fuel procurement costs and adjust delivery schedules. Consider advance purchases if trend continues.",
                'power cut': "Prepare backup power systems. Adjust operational hours to minimize impact on critical processes.",
                'flood warning': "Secure ground-floor inventory. Review supply chain routes for weather-related disruptions.",
                'protest': "Monitor locations for potential transport delays. Consider remote work options for affected areas.",
            },
            'supply_chain': {
                'fuel prices': "Fuel cost increases may impact logistics. Review vendor contracts and consider bulk purchasing.",
                'road conditions': "Plan alternative routes for deliveries. Communicate potential delays to customers.",
                'monsoon rain': "Weather may affect supply chain. Increase buffer stock for essential items.",
            },
            'market_opportunity': {
                'tourism boost': "Increased tourism detected. Consider marketing campaigns targeting visitors.",
                'tech startup': "Growing tech sector activity. Potential B2B opportunities or partnerships.",
            }
        }
    
    def generate_insights(self, signals: List[Signal]) -> List[Insight]:
        """Generate insights from detected signals"""
        insights = []
        
        # Group signals by topic
        topic_signals = {}
        for signal in signals:
            if signal.topic not in topic_signals:
                topic_signals[signal.topic] = []
            topic_signals[signal.topic].append(signal)
        
        # Generate insights per topic
        for topic, topic_sigs in topic_signals.items():
            # Skip low-priority topics
            if len(topic_sigs) < 1:
                continue
            
            # Determine insight type based on signals
            urgency_levels = [s.urgency for s in topic_sigs]
            has_high_urgency = any(u in ['critical', 'high'] for u in urgency_levels)
            
            if has_high_urgency:
                insight = self._create_operational_risk_insight(topic, topic_sigs)
            else:
                insight = self._create_awareness_insight(topic, topic_sigs)
            
            if insight:
                insights.append(insight)
        
        # Generate cross-topic insights
        cross_insights = self._generate_cross_topic_insights(signals)
        insights.extend(cross_insights)
        
        return insights
    
    def _create_operational_risk_insight(self, topic: str, signals: List[Signal]) -> Insight:
        """Create operational risk insight"""
        # Calculate severity
        urgencies = [s.urgency for s in signals]
        if 'critical' in urgencies:
            severity = 'critical'
        elif 'high' in urgencies:
            severity = 'critical'
        else:
            severity = 'warning'
        
        # Extract affected locations
        locations = []
        for signal in signals:
            if 'location' in signal.metadata:
                locations.append(signal.metadata['location'])
        
        # Get recommendation
        recommendation = self._get_recommendation(topic, 'operational_risk')
        
        # Calculate confidence (average of signal confidences)
        avg_confidence = sum(s.confidence_score for s in signals) / len(signals)
        
        insight = Insight(
            insight_id=str(uuid.uuid4()),
            insight_type='operational_risk',
            title=f"Operational Risk: {topic.title()}",
            description=f"Detected {len(signals)} signals indicating {topic} requires attention. "
                       f"This may impact business operations in the near term.",
            severity=severity,
            affected_areas=list(set(locations)) if locations else ['National'],
            recommendation=recommendation,
            supporting_signals=signals,
            confidence=avg_confidence,
            created_at=datetime.now(),
            valid_until=datetime.now() + timedelta(hours=48)
        )
        
        return insight
    
    def _create_awareness_insight(self, topic: str, signals: List[Signal]) -> Insight:
        """Create general awareness insight"""
        total_mentions = sum(s.source_count for s in signals)
        
        insight = Insight(
            insight_id=str(uuid.uuid4()),
            insight_type='situational_awareness',
            title=f"Public Attention: {topic.title()}",
            description=f"{topic.title()} mentioned {total_mentions} times across sources. "
                       f"Monitor for potential business implications.",
            severity='info',
            affected_areas=['National'],
            recommendation=f"Continue monitoring {topic}. No immediate action required.",
            supporting_signals=signals,
            confidence=70,
            created_at=datetime.now(),
            valid_until=datetime.now() + timedelta(hours=24)
        )
        
        return insight
    
    def _generate_cross_topic_insights(self, signals: List[Signal]) -> List[Insight]:
        """Generate insights from patterns across multiple topics"""
        insights = []
        
        # Check for correlated economic issues
        economic_topics = ['fuel prices', 'inflation', 'rupee exchange rate']
        economic_signals = [s for s in signals if s.topic in economic_topics]
        
        if len(economic_signals) >= 2:
            insight = Insight(
                insight_id=str(uuid.uuid4()),
                insight_type='economic_pressure',
                title="Economic Pressure Indicators",
                description=f"Multiple economic indicators showing activity: "
                           f"{', '.join(set(s.topic for s in economic_signals))}. "
                           f"Suggests broader economic challenges.",
                severity='warning',
                affected_areas=['National'],
                recommendation="Review pricing strategies, cost management, and cash flow projections. "
                              "Consider hedging against currency fluctuations if applicable.",
                supporting_signals=economic_signals,
                confidence=80,
                created_at=datetime.now(),
                valid_until=datetime.now() + timedelta(days=7)
            )
            insights.append(insight)
        
        # Check for infrastructure clustering
        infrastructure_topics = ['power cut', 'road conditions', 'public transport', 'water shortage']
        infra_signals = [s for s in signals if s.topic in infrastructure_topics]
        
        if len(infra_signals) >= 2:
            insight = Insight(
                insight_id=str(uuid.uuid4()),
                insight_type='infrastructure_stress',
                title="Infrastructure Challenges Detected",
                description=f"Multiple infrastructure issues reported: "
                           f"{', '.join(set(s.topic for s in infra_signals))}. "
                           f"May affect operations and logistics.",
                severity='warning',
                affected_areas=['National'],
                recommendation="Prepare contingency plans for operational disruptions. "
                              "Consider alternative work arrangements and delivery schedules.",
                supporting_signals=infra_signals,
                confidence=75,
                created_at=datetime.now(),
                valid_until=datetime.now() + timedelta(days=3)
            )
            insights.append(insight)
        
        return insights
    
    def _get_recommendation(self, topic: str, insight_type: str) -> str:
        """Get recommendation for topic and type"""
        if insight_type in self.insight_templates and topic in self.insight_templates[insight_type]:
            return self.insight_templates[insight_type][topic]
        
        # Default recommendations
        defaults = {
            'operational_risk': f"Monitor {topic} closely. Assess potential impact on operations and prepare mitigation strategies.",
            'supply_chain': f"Review supply chain dependencies related to {topic}. Identify alternative suppliers if needed.",
            'market_opportunity': f"Evaluate opportunities related to {topic}. Consider strategic initiatives to capitalize on trend."
        }
        
        return defaults.get(insight_type, f"Monitor {topic} and assess business implications.")

if __name__ == "__main__":
    from analytics.detectors.pattern_detector import PatternDetector
    
    detector = PatternDetector()
    results = detector.run_all_detectors()
    detector.close()
    
    # Flatten signals
    all_signals = []
    for signals in results.values():
        all_signals.extend(signals)
    
    # Generate insights
    generator = InsightGenerator()
    insights = generator.generate_insights(all_signals)
    
    print("\n" + "="*70)
    print("💡 BUSINESS INSIGHTS GENERATED")
    print("="*70)
    
    for i, insight in enumerate(insights, 1):
        print(f"\n{i}. [{insight.severity.upper()}] {insight.title}")
        print(f"   {insight.description}")
        print(f"   Recommendation: {insight.recommendation}")
        print(f"   Confidence: {insight.confidence:.0f}%")
        if insight.affected_areas:
            print(f"   Affected Areas: {', '.join(insight.affected_areas)}")