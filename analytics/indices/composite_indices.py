"""
Composite Business Indices
Combines multiple signals into single actionable scores
INNOVATION: Multi-signal aggregation for business decision-making
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import List, Dict
from analytics.models import Signal

class CompositeIndexCalculator:
    """
    Calculate composite indices from multiple signals
    These are business-friendly scores (0-100) that aggregate multiple indicators
    """
    
    # Define topic categories
    ECONOMIC_TOPICS = [
        'fuel prices', 'inflation', 'rupee exchange rate', 
        'economy', 'salary', 'cost'
    ]
    
    INFRASTRUCTURE_TOPICS = [
        'power cut', 'road conditions', 'public transport', 
        'water shortage', 'electricity', 'transport'
    ]
    
    WEATHER_TOPICS = [
        'monsoon rain', 'flood warning', 'drought', 
        'weather', 'rainfall', 'cyclone'
    ]
    
    POLITICAL_TOPICS = [
        'protest', 'government policy', 'election', 
        'parliament', 'demonstration'
    ]
    
    # Urgency score mapping
    URGENCY_SCORES = {
        'critical': 100,
        'high': 75,
        'medium': 50,
        'low': 25
    }
    
    def calculate_economic_stress_index(self, signals: List[Signal]) -> Dict:
        """
        Economic Stress Index (0-100)
        Measures pressure from economic factors
        
        High score = businesses should prepare for economic challenges
        """
        economic_signals = [
            s for s in signals 
            if any(topic in s.topic.lower() for topic in self.ECONOMIC_TOPICS)
        ]
        
        if not economic_signals:
            return {
                'score': 0,
                'level': 'LOW',
                'signal_count': 0,
                'description': 'No economic stress detected'
            }
        
        # Calculate weighted score
        total_score = sum(
            self.URGENCY_SCORES.get(s.urgency, 0) * (s.confidence_score / 100)
            for s in economic_signals
        )
        
        # Normalize to 0-100
        max_possible = len(economic_signals) * 100
        index = (total_score / max_possible * 100) if max_possible > 0 else 0
        
        # Determine level
        if index >= 70:
            level = 'CRITICAL'
            description = 'Severe economic pressure detected. Review pricing, costs, and cash flow urgently.'
        elif index >= 50:
            level = 'HIGH'
            description = 'Elevated economic concerns. Monitor closely and prepare contingency plans.'
        elif index >= 30:
            level = 'MEDIUM'
            description = 'Moderate economic activity. Stay informed of developments.'
        else:
            level = 'LOW'
            description = 'Economic conditions relatively stable.'
        
        return {
            'score': round(index, 1),
            'level': level,
            'signal_count': len(economic_signals),
            'description': description,
            'top_concerns': list(set(s.topic for s in economic_signals[:3]))
        }
    
    def calculate_operational_risk_index(self, signals: List[Signal]) -> Dict:
        """
        Operational Risk Index (0-100)
        Measures disruption risk to business operations
        
        High score = expect operational disruptions
        """
        operational_signals = [
            s for s in signals 
            if any(topic in s.topic.lower() for topic in self.INFRASTRUCTURE_TOPICS)
        ]
        
        if not operational_signals:
            return {
                'score': 0,
                'level': 'LOW',
                'signal_count': 0,
                'description': 'No operational risks detected'
            }
        
        # Weight by urgency and source count
        total_score = sum(
            self.URGENCY_SCORES.get(s.urgency, 0) * 
            (s.confidence_score / 100) * 
            min(1.5, 1 + (s.source_count / 100))  # Volume boost
            for s in operational_signals
        )
        
        max_possible = len(operational_signals) * 100 * 1.5
        index = (total_score / max_possible * 100) if max_possible > 0 else 0
        
        if index >= 70:
            level = 'CRITICAL'
            description = 'Major operational disruptions likely. Activate contingency plans.'
        elif index >= 50:
            level = 'HIGH'
            description = 'Significant operational challenges. Prepare backup systems.'
        elif index >= 30:
            level = 'MEDIUM'
            description = 'Some operational risks present. Monitor infrastructure status.'
        else:
            level = 'LOW'
            description = 'Operations likely to proceed normally.'
        
        return {
            'score': round(index, 1),
            'level': level,
            'signal_count': len(operational_signals),
            'description': description,
            'top_concerns': list(set(s.topic for s in operational_signals[:3]))
        }
    
    def calculate_weather_impact_index(self, signals: List[Signal]) -> Dict:
        """
        Weather Impact Index (0-100)
        Measures potential disruption from weather events
        """
        weather_signals = [
            s for s in signals 
            if any(topic in s.topic.lower() for topic in self.WEATHER_TOPICS)
        ]
        
        if not weather_signals:
            return {
                'score': 0,
                'level': 'LOW',
                'signal_count': 0,
                'description': 'No weather concerns'
            }
        
        total_score = sum(
            self.URGENCY_SCORES.get(s.urgency, 0) * (s.confidence_score / 100)
            for s in weather_signals
        )
        
        max_possible = len(weather_signals) * 100
        index = (total_score / max_possible * 100) if max_possible > 0 else 0
        
        if index >= 70:
            level = 'CRITICAL'
            description = 'Severe weather threat. Secure assets and review supply chains.'
        elif index >= 50:
            level = 'HIGH'
            description = 'Significant weather concerns. Prepare for potential disruptions.'
        elif index >= 30:
            level = 'MEDIUM'
            description = 'Weather may affect operations. Stay alert.'
        else:
            level = 'LOW'
            description = 'Weather conditions manageable.'
        
        return {
            'score': round(index, 1),
            'level': level,
            'signal_count': len(weather_signals),
            'description': description,
            'top_concerns': list(set(s.topic for s in weather_signals[:3]))
        }
    
    def calculate_social_unrest_index(self, signals: List[Signal]) -> Dict:
        """
        Social Unrest Index (0-100)
        Measures potential for social disruption
        """
        political_signals = [
            s for s in signals 
            if any(topic in s.topic.lower() for topic in self.POLITICAL_TOPICS)
        ]
        
        if not political_signals:
            return {
                'score': 0,
                'level': 'LOW',
                'signal_count': 0,
                'description': 'Social environment stable'
            }
        
        # Consider both urgency and volume (protests spreading = higher risk)
        total_score = sum(
            self.URGENCY_SCORES.get(s.urgency, 0) * 
            (s.confidence_score / 100) *
            (1 + (s.source_count / 50))  # Volume matters for protests
            for s in political_signals
        )
        
        max_possible = len(political_signals) * 100 * 2
        index = (total_score / max_possible * 100) if max_possible > 0 else 0
        
        if index >= 70:
            level = 'CRITICAL'
            description = 'High social unrest. Avoid affected areas, consider remote work.'
        elif index >= 50:
            level = 'HIGH'
            description = 'Elevated social activity. Monitor for transport disruptions.'
        elif index >= 30:
            level = 'MEDIUM'
            description = 'Some social unrest. Stay informed of developments.'
        else:
            level = 'LOW'
            description = 'Social environment relatively calm.'
        
        return {
            'score': round(index, 1),
            'level': level,
            'signal_count': len(political_signals),
            'description': description,
            'top_concerns': list(set(s.topic for s in political_signals[:3]))
        }
    
    def calculate_all_indices(self, signals: List[Signal]) -> Dict[str, Dict]:
        """
        Calculate all composite indices
        
        Returns:
            Dictionary with all index scores and metadata
        """
        return {
            'economic_stress': self.calculate_economic_stress_index(signals),
            'operational_risk': self.calculate_operational_risk_index(signals),
            'weather_impact': self.calculate_weather_impact_index(signals),
            'social_unrest': self.calculate_social_unrest_index(signals)
        }
    
    def get_overall_business_risk_score(self, signals: List[Signal]) -> Dict:
        """
        Overall Business Risk Score
        Master score combining all indices
        """
        all_indices = self.calculate_all_indices(signals)
        
        # Weighted average (economic and operational matter more)
        weights = {
            'economic_stress': 0.35,
            'operational_risk': 0.35,
            'weather_impact': 0.15,
            'social_unrest': 0.15
        }
        
        overall_score = sum(
            all_indices[key]['score'] * weights[key]
            for key in weights.keys()
        )
        
        if overall_score >= 70:
            level = 'CRITICAL'
            action = 'Activate full business continuity plan. Senior leadership should convene.'
        elif overall_score >= 50:
            level = 'HIGH'
            action = 'Heightened alert. Review all contingency plans and prepare for disruption.'
        elif overall_score >= 30:
            level = 'MEDIUM'
            action = 'Monitor situation closely. Brief teams on potential developments.'
        else:
            level = 'LOW'
            action = 'Maintain normal operations. Continue routine monitoring.'
        
        return {
            'overall_score': round(overall_score, 1),
            'level': level,
            'action': action,
            'component_scores': {
                key: data['score'] for key, data in all_indices.items()
            }
        }


def display_indices(indices: Dict):
    """Pretty print the indices"""
    print("\n" + "="*70)
    print("📊 COMPOSITE BUSINESS INDICES")
    print("="*70)
    
    # Individual indices
    for name, data in indices.items():
        if name == 'overall_risk':
            continue
            
        score = data['score']
        level = data['level']
        
        # Visual indicator
        if level == 'CRITICAL':
            icon = "🔴"
            bar = "█" * int(score / 2)
        elif level == 'HIGH':
            icon = "🟠"
            bar = "█" * int(score / 2)
        elif level == 'MEDIUM':
            icon = "🟡"
            bar = "█" * int(score / 2)
        else:
            icon = "🟢"
            bar = "█" * int(score / 2)
        
        print(f"\n{icon} {name.replace('_', ' ').title()}")
        print(f"   Score: {score:5.1f}/100 [{bar}]")
        print(f"   Level: {level}")
        print(f"   Signals: {data['signal_count']}")
        print(f"   {data['description']}")
        
        if data.get('top_concerns'):
            print(f"   Top Concerns: {', '.join(data['top_concerns'])}")


if __name__ == "__main__":
    from analytics.detectors.pattern_detector import PatternDetector
    
    print("🔍 Running pattern detection...")
    detector = PatternDetector()
    results = detector.run_all_detectors()
    detector.close()
    
    # Flatten all signals
    all_signals = []
    for signals in results.values():
        all_signals.extend(signals)
    
    # Calculate indices
    calculator = CompositeIndexCalculator()
    indices = calculator.calculate_all_indices(all_signals)
    
    # Display
    display_indices(indices)
    
    # Overall risk
    print("\n" + "="*70)
    print("🎯 OVERALL BUSINESS RISK ASSESSMENT")
    print("="*70)
    
    overall = calculator.get_overall_business_risk_score(all_signals)
    
    score = overall['overall_score']
    level = overall['level']
    icon = "🔴" if level == 'CRITICAL' else "🟠" if level == 'HIGH' else "🟡" if level == 'MEDIUM' else "🟢"
    
    print(f"\n{icon} Overall Risk Score: {score:.1f}/100")
    print(f"   Risk Level: {level}")
    print(f"   Recommended Action: {overall['action']}")
    
    print("\n   Component Breakdown:")
    for component, comp_score in overall['component_scores'].items():
        print(f"      • {component.replace('_', ' ').title()}: {comp_score:.1f}/100")
    
    print("\n" + "="*70 + "\n")