"""
Core data models for analytics
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

@dataclass
class Signal:
    """Detected signal/pattern in data"""
    signal_id: str
    signal_type: str  # 'spike', 'trend', 'anomaly', 'sentiment_shift'
    topic: str
    description: str
    urgency: str  # 'low', 'medium', 'high', 'critical'
    confidence_score: float  # 0-100
    source_count: int
    first_seen: datetime
    last_seen: datetime
    metadata: Dict = field(default_factory=dict)

@dataclass
class Insight:
    """Business insight generated from signals"""
    insight_id: str
    insight_type: str  # 'operational_risk', 'opportunity', 'alert', 'trend'
    title: str
    description: str
    severity: str  # 'info', 'warning', 'critical'
    affected_areas: List[str]
    recommendation: str
    supporting_signals: List[Signal]
    confidence: float
    created_at: datetime
    valid_until: Optional[datetime] = None
    
@dataclass
class TopicMetrics:
    """Metrics for a specific topic"""
    topic: str
    mention_count: int
    urgency_breakdown: Dict[str, int]
    sentiment_breakdown: Dict[str, int]
    geographic_distribution: Dict[str, int]
    hourly_trend: List[Dict]
    velocity: float  # mentions per hour
    spike_detected: bool