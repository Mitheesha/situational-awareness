"""
Analytics Engine - Main Orchestrator
Runs complete analytics pipeline and stores results
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
from analytics.detectors.pattern_detector import PatternDetector
from analytics.scorers.signal_scorer import SignalScorer
from analytics.generators.insight_generator import InsightGenerator
from pipeline.models.database import Database

class AnalyticsEngine:
    """Main analytics engine orchestrator"""
    
    def __init__(self):
        self.detector = PatternDetector()
        self.scorer = SignalScorer()
        self.generator = InsightGenerator()
        self.db = Database()
        self.db.connect()
    
    def run_full_analysis(self):
        """Run complete analytics pipeline"""
        print("\n" + "="*70)
        print("🧠 ANALYTICS ENGINE - LAYER 3")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Step 1: Detect patterns
        print("\n📍 STEP 1: PATTERN DETECTION")
        pattern_results = self.detector.run_all_detectors()
        
        # Flatten signals
        all_signals = []
        for signals in pattern_results.values():
            all_signals.extend(signals)
        
        print(f"\n✅ Total patterns detected: {len(all_signals)}")
        
        # Step 2: Score and rank
        print("\n📍 STEP 2: SIGNAL SCORING")
        ranked_signals = self.scorer.rank_signals(all_signals)
        priority_signals = self.scorer.get_priority_signals(all_signals, top_n=15)
        
        print(f"✅ Signals scored and ranked")
        print(f"✅ Top {len(priority_signals)} priority signals identified")
        
        # Step 3: Generate insights
        print("\n📍 STEP 3: INSIGHT GENERATION")
        insights = self.generator.generate_insights(priority_signals)
        
        print(f"✅ {len(insights)} business insights generated")
        
        # Step 4: Store in database
        print("\n📍 STEP 4: STORING RESULTS")
        self._store_signals(all_signals)
        self._store_insights(insights)
        
        print(f"✅ Results stored in database")
        
        # Step 5: Display results
        self._display_results(ranked_signals, insights)
        
        print("\n" + "="*70)
        print("✅ ANALYTICS COMPLETE")
        print("="*70)
        
        return {
            'signals': all_signals,
            'ranked_signals': ranked_signals,
            'insights': insights
        }
    
    def _store_signals(self, signals):
        """Store detected signals in database"""
        with self.db.get_cursor() as cursor:
            for signal in signals:
                cursor.execute("""
                    INSERT INTO signals 
                    (signal_type, topic, description, urgency, confidence_score,
                     source_count, first_seen, last_seen, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    signal.signal_type,
                    signal.topic,
                    signal.description,
                    signal.urgency,
                    signal.confidence_score,
                    signal.source_count,
                    signal.first_seen,
                    signal.last_seen,
                    json.dumps(signal.metadata)
                ))
    
    def _store_insights(self, insights):
        """Store generated insights in database"""
        with self.db.get_cursor() as cursor:
            for insight in insights:
                cursor.execute("""
                    INSERT INTO insights
                    (insight_type, title, description, severity, affected_areas,
                     recommendation, supporting_data, created_at, valid_until)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    insight.insight_type,
                    insight.title,
                    insight.description,
                    insight.severity,
                    insight.affected_areas,
                    insight.recommendation,
                    json.dumps({'confidence': insight.confidence}),
                    insight.created_at,
                    insight.valid_until
                ))
    
    def _display_results(self, ranked_signals, insights):
        """Display analysis results"""
        print("\n" + "="*70)
        print("🎯 TOP 10 PRIORITY SIGNALS")
        print("="*70)
        
        for i, (signal, score) in enumerate(ranked_signals[:10], 1):
            print(f"\n{i}. [{signal.signal_type.upper()}] {signal.topic}")
            print(f"   Score: {score:.1f}/100 | Urgency: {signal.urgency}")
            print(f"   {signal.description[:80]}...")
        
        print("\n" + "="*70)
        print("💡 BUSINESS INSIGHTS")
        print("="*70)
        
        critical = [i for i in insights if i.severity == 'critical']
        warnings = [i for i in insights if i.severity == 'warning']
        
        if critical:
            print("\n🚨 CRITICAL:")
            for insight in critical:
                print(f"   • {insight.title}")
                print(f"     {insight.recommendation[:100]}...")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for insight in warnings:
                print(f"   • {insight.title}")
    
    def close(self):
        """Cleanup"""
        self.detector.close()
        self.db.disconnect()

if __name__ == "__main__":
    import json
    engine = AnalyticsEngine()
    results = engine.run_full_analysis()
    engine.close()