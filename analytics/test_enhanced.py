"""
Test all enhanced analytics features
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from analytics.run_analytics import AnalyticsEngine

if __name__ == "__main__":
    print("🚀 Testing Enhanced Analytics Features...")
    print("="*70)
    
    engine = AnalyticsEngine()
    
    # Run enhanced analysis
    results = engine.run_enhanced_analysis()
    
    engine.close()
    
    print("\n✅ All enhanced features tested successfully!")
    print("\n📊 Results Summary:")
    print(f"   • Signals: {len(results['signals'])}")
    print(f"   • Indices: {len(results['indices'])}")
    print(f"   • Velocities: {len(results['velocities'])}")
    print(f"   • Warnings: {len(results['warnings'])}")
    print(f"   • Insights: {len(results['insights'])}")
    print(f"   • Overall Risk: {results['overall_risk']['overall_score']:.1f}/100")