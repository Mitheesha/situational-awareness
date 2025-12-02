"""
Signal Scoring - Rates importance and priority of detected signals
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import List
from analytics.models import Signal

class SignalScorer:
    """Scores and prioritizes detected signals"""
    
    # Urgency weights
    URGENCY_WEIGHTS = {
        'critical': 100,
        'high': 75,
        'medium': 50,
        'low': 25
    }
    
    # Signal type weights
    TYPE_WEIGHTS = {
        'spike': 1.2,
        'trend': 0.9,
        'sentiment_shift': 1.1,
        'geographic_hotspot': 1.0,
        'anomaly': 1.3
    }
    
    def score_signal(self, signal: Signal) -> float:
        """
        Calculate comprehensive score for a signal (0-100)
        
        Factors:
        - Urgency level
        - Signal type
        - Confidence score
        - Source count (volume)
        - Recency
        """
        # Base score from urgency
        base_score = self.URGENCY_WEIGHTS.get(signal.urgency, 25)
        
        # Type multiplier
        type_mult = self.TYPE_WEIGHTS.get(signal.signal_type, 1.0)
        
        # Confidence factor (0.5 - 1.0)
        confidence_factor = 0.5 + (signal.confidence_score / 200)
        
        # Volume factor (logarithmic scaling)
        import math
        volume_factor = min(1.5, 1 + math.log10(max(1, signal.source_count)) / 10)
        
        # Calculate final score
        final_score = base_score * type_mult * confidence_factor * volume_factor
        
        return min(100, max(0, final_score))
    
    def rank_signals(self, signals: List[Signal]) -> List[tuple]:
        """
        Rank signals by score
        
        Returns:
            List of (signal, score) tuples, sorted by score descending
        """
        scored = [(signal, self.score_signal(signal)) for signal in signals]
        return sorted(scored, key=lambda x: x[1], reverse=True)
    
    def filter_by_threshold(self, signals: List[Signal], threshold: float = 60) -> List[Signal]:
        """Return only signals above threshold score"""
        return [s for s in signals if self.score_signal(s) >= threshold]
    
    def get_priority_signals(self, signals: List[Signal], top_n: int = 10) -> List[Signal]:
        """Get top N highest-priority signals"""
        ranked = self.rank_signals(signals)
        return [signal for signal, score in ranked[:top_n]]

if __name__ == "__main__":
    # Test with pattern detector
    from analytics.detectors.pattern_detector import PatternDetector
    
    detector = PatternDetector()
    results = detector.run_all_detectors()
    detector.close()
    
    # Flatten all signals
    all_signals = []
    for signals in results.values():
        all_signals.extend(signals)
    
    # Score and rank
    scorer = SignalScorer()
    ranked = scorer.rank_signals(all_signals)
    
    print("\n" + "="*70)
    print("🎯 TOP 10 PRIORITY SIGNALS")
    print("="*70)
    
    for i, (signal, score) in enumerate(ranked[:10], 1):
        print(f"\n{i}. [{signal.signal_type.upper()}] {signal.topic}")
        print(f"   Score: {score:.1f}/100 | Urgency: {signal.urgency} | Confidence: {signal.confidence_score:.0f}%")
        print(f"   {signal.description}")