"""
🇱🇰 Situational Awareness Platform - Main Dashboard
Real-time intelligence for Sri Lankan businesses
"""

import streamlit as st

st.set_page_config(
    page_title="Situational Awareness Platform",
    page_icon="🇱🇰",
    layout="wide",
    initial_sidebar_state="expanded"
)



import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pipeline.models.database import Database

# Initialize database connection
@st.cache_resource
def get_database():
    db = Database()
    if db.connect():
        return db
    return None

db = get_database()

# Check if database is connected
if db is None:
    st.error("""
    🚨 **Database Connection Failed**
    
    Please start the infrastructure:
```
    cd infra
    docker compose up -d
```
    
    Then refresh this page.
    """)
    st.stop()

# Page configuration


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .alert-critical {
        background-color: #ff4444;
        padding: 1rem;
        border-radius: 5px;
        color: white;
        margin: 0.5rem 0;
    }
    .alert-high {
        background-color: #ff8800;
        padding: 1rem;
        border-radius: 5px;
        color: white;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# Header
st.markdown('<h1 class="main-header">🇱🇰 Situational Awareness Platform</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Real-time Intelligence for Sri Lankan Businesses | Powered by AI/ML</p>', unsafe_allow_html=True)

# Sidebar filters
st.sidebar.title("🎛️ Controls")
time_range = st.sidebar.selectbox(
    "📅 Time Range",
    ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
    index=0
)

# Convert to hours
time_map = {
    "Last 24 Hours": 24,
    "Last 7 Days": 168,
    "Last 30 Days": 720,
    "All Time": None
}
hours = time_map[time_range]

source_filter = st.sidebar.multiselect(
    "📰 Data Sources",
    ["Ada Derana", "The Island", "X (Twitter) [Simulated]"],
    default=["Ada Derana", "The Island", "X (Twitter) [Simulated]"]
)

st.sidebar.markdown("---")
refresh = st.sidebar.button("🔄 Refresh Data")

#Fetch Data
@st.cache_data(ttl=300)
def load_dashboard_data(hours, sources):
    """Load all dashboard data"""
    
    db = Database()
    db.connect()
    
    try:
        with db.get_cursor(dict_cursor=True) as cursor:
            # Build filters ONCE
            rd_time_filter = ""
            sp_time_filter = ""
            if hours:
                rd_time_filter = f"AND rd.created_at > NOW() - INTERVAL '{hours} hours'"
                sp_time_filter = f"AND sp.created_at > NOW() - INTERVAL '{hours} hours'"
            
            source_filter_sql = ""
            if sources:
                source_list = "', '".join(sources)
                source_filter_sql = f"AND rd.source IN ('{source_list}')"
            
            # Overall stats
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT rd.source) as sources,
                    AVG(CAST(rd.metadata->>'ai_sentiment_score' AS FLOAT)) as avg_sentiment,
                    COUNT(CASE WHEN rd.source_type = 'news' THEN 1 END) as news_count,
                    COUNT(CASE WHEN rd.source_type = 'social' THEN 1 END) as social_count
                FROM raw_data rd
                WHERE 1=1 {rd_time_filter} {source_filter_sql}
            """)
            stats = cursor.fetchone()
            
            # Sentiment timeline
            cursor.execute(f"""
                SELECT 
                    DATE_TRUNC('hour', rd.created_at) as hour,
                    AVG(CAST(rd.metadata->>'ai_sentiment_score' AS FLOAT)) as avg_sentiment,
                    COUNT(*) as count
                FROM raw_data rd
                WHERE rd.metadata->>'ai_sentiment_score' IS NOT NULL
                {rd_time_filter} {source_filter_sql}
                GROUP BY DATE_TRUNC('hour', rd.created_at)
                ORDER BY hour DESC
                LIMIT 48
            """)
            sentiment_timeline = cursor.fetchall()
            
            # Top topics
            cursor.execute(f"""
                SELECT 
                    sp.topic,
                    sp.urgency,
                    COUNT(*) as mentions,
                    AVG(CAST(rd.metadata->>'ai_sentiment_score' AS FLOAT)) as avg_sentiment
                FROM social_posts sp
                JOIN raw_data rd ON sp.raw_data_id = rd.id
                WHERE 1=1 {sp_time_filter}
                GROUP BY sp.topic, sp.urgency
                ORDER BY mentions DESC
                LIMIT 10
            """)
            top_topics = cursor.fetchall()
            
            # Geographic distribution
            cursor.execute(f"""
                SELECT 
                    sp.location,
                    COUNT(*) as mentions,
                    AVG(CAST(rd.metadata->>'ai_sentiment_score' AS FLOAT)) as avg_sentiment
                FROM social_posts sp
                JOIN raw_data rd ON sp.raw_data_id = rd.id
                WHERE sp.location IS NOT NULL {sp_time_filter}
                GROUP BY sp.location
                ORDER BY mentions DESC
            """)
            locations = cursor.fetchall()
            
            # Recent alerts
            cursor.execute(f"""
                SELECT 
                    rd.title,
                    rd.source,
                    sp.topic,
                    COALESCE(sp.urgency, 'medium') as urgency,
                    CAST(rd.metadata->>'ai_sentiment_score' AS FLOAT) as sentiment,
                    sp.created_at as fetched_at
                FROM raw_data rd
                JOIN social_posts sp ON sp.raw_data_id = rd.id
                WHERE COALESCE(sp.urgency, 'medium') IN ('critical', 'high')
                  AND CAST(rd.metadata->>'ai_sentiment_score' AS FLOAT) < -0.3
                  {sp_time_filter}
                ORDER BY sp.created_at DESC
                LIMIT 10
            """)
            alerts = cursor.fetchall()
        
        return {
            'stats': stats,
            'sentiment_timeline': sentiment_timeline,
            'top_topics': top_topics,
            'locations': locations,
            'alerts': alerts
        }
    
    finally:
        db.disconnect()

# Load data
data = load_dashboard_data(hours, source_filter)

# Top metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📊 Total Records",
        f"{data['stats']['total_records']:,}",
        delta=None
    )

with col2:
    sentiment_score = data['stats']['avg_sentiment'] or 0
    sentiment_emoji = "🟢" if sentiment_score > 0 else "🔴" if sentiment_score < -0.2 else "🟡"
    st.metric(
        "😊 AI Sentiment",
        f"{sentiment_emoji} {sentiment_score:.3f}",
        delta=f"{'Positive' if sentiment_score > 0 else 'Negative'}"
    )

with col3:
    st.metric(
        "📰 News Articles",
        f"{data['stats']['news_count']:,}",
        delta=None
    )

with col4:
    st.metric(
        "🐦 Social Posts",
        f"{data['stats']['social_count']:,}",
        delta=None
    )

st.markdown("---")

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🤖 AI Insights",
    "🚨 Alerts",
    "🗺️ Geographic",
    "📈 Analytics"
])

# TAB 1: Overview
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 AI Sentiment Trend")
        
        if data['sentiment_timeline']:
            df_sentiment = pd.DataFrame(data['sentiment_timeline'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_sentiment['hour'],
                y=df_sentiment['avg_sentiment'],
                mode='lines+markers',
                name='Sentiment',
                line=dict(color='#1f77b4', width=3),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.2)'
            ))
            
            fig.add_hline(y=0, line_dash="dash", line_color="red", 
                         annotation_text="Neutral")
            
            fig.update_layout(
                height=400,
                xaxis_title="Time",
                yaxis_title="AI Sentiment Score",
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sentiment data available for selected time range")
    
    with col2:
        st.subheader("🔥 Top Topics")
        
        if data['top_topics']:
            for topic in data['top_topics'][:5]:
                urgency_color = {
                                    'critical': '🔴',
                                    'high': '🟠',
                                    'medium': '🟡',
                                    'low': '🟢'
                                }.get(topic.get('urgency') or 'medium', '⚪')
                
                st.markdown(f"""
                <div style="background: #f0f2f6; padding: 1rem; border-radius: 5px; margin: 0.5rem 0;">
                    <b>{urgency_color} {topic['topic'].title()}</b><br>
                    <span style="font-size: 0.9rem; color: #666;">
                        {topic['mentions']} mentions | Sentiment: {topic['avg_sentiment']:.2f}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No topic data available")

# TAB 2: AI Insights
with tab2:
    st.subheader("🤖 AI-Powered Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💡 Key Insights")
        
        # Calculate insights from data
        avg_sent = data['stats']['avg_sentiment'] or 0
        
        if avg_sent < -0.3:
            st.error("🔴 **Critical**: Overall public sentiment is very negative")
            st.markdown("**AI Recommendation**: Monitor for potential disruptions. Review crisis communication plans.")
        elif avg_sent < -0.1:
            st.warning("🟠 **Warning**: Public sentiment trending negative")
            st.markdown("**AI Recommendation**: Investigate root causes. Prepare contingency plans.")
        else:
            st.success("🟢 **Stable**: Public sentiment is neutral to positive")
            st.markdown("**AI Recommendation**: Maintain current operations. Continue monitoring.")
        
        st.markdown("---")
        
        # Top risk topics
        if data['top_topics']:
            st.markdown("### ⚠️ Risk Topics")
            high_risk = [t for t in data['top_topics'] if t['urgency'] in ['critical', 'high']]
            
            if high_risk:
                for topic in high_risk[:3]:
                    st.markdown(f"""
                    - **{topic['topic'].title()}**: {topic['mentions']} mentions (Urgency: {topic['urgency'].upper()})
                    """)
            else:
                st.info("No high-risk topics detected")
    
    with col2:
        st.markdown("### 📊 AI Model Performance")
        
        # Create gauge chart for AI confidence
        confidence = 0.867  # From your sentiment analysis
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=confidence * 100,
            title={'text': "AI Confidence Score"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 60], 'color': "lightgray"},
                    {'range': [60, 80], 'color': "gray"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        **Model Details:**
        - Sentiment: DistilBERT Transformer
        - Anomaly Detection: Isolation Forest
        - Training Data: 10,000+ records
        - Accuracy: 86.7%
        """)

# TAB 3: Alerts
with tab3:
    st.subheader("🚨 Priority Alerts")
    
    if data['alerts']:
        for alert in data['alerts']:
            sentiment_emoji = "🔴" if alert['sentiment'] < -0.5 else "🟠"
            urgency_badge = alert['urgency'].upper()
            
            st.markdown(f"""
            <div class="alert-{'critical' if alert['urgency'] == 'critical' else 'high'}">
                <b>{sentiment_emoji} [{urgency_badge}] {alert['topic'].title()}</b><br>
                <i>{alert['title'][:100]}...</i><br>
                <small>Source: {alert['source']} | Time: {alert['fetched_at'].strftime('%Y-%m-%d %H:%M')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No critical alerts at this time")
    
    st.markdown("---")
    
    # Alert statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        critical_count = sum(1 for a in data['alerts'] if a['urgency'] == 'critical')
        st.metric("🔴 Critical", critical_count)
    
    with col2:
        high_count = sum(1 for a in data['alerts'] if a['urgency'] == 'high')
        st.metric("🟠 High", high_count)
    
    with col3:
        st.metric("📊 Total Alerts", len(data['alerts']))

# TAB 4: Geographic
with tab4:
    st.subheader("🗺️ Geographic Distribution")
    
    if data['locations']:
        df_locations = pd.DataFrame(data['locations'])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Bar chart
            fig = px.bar(
                df_locations,
                x='location',
                y='mentions',
                color='avg_sentiment',
                color_continuous_scale=['red', 'yellow', 'green'],
                title='Mentions by Location',
                labels={'mentions': 'Number of Mentions', 'location': 'Location'}
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📍 Location Summary")
            
            for loc in df_locations.head(5).itertuples():
                sentiment_emoji = "🟢" if loc.avg_sentiment > 0 else "🔴" if loc.avg_sentiment < -0.2 else "🟡"
                st.markdown(f"""
                **{sentiment_emoji} {loc.location}**  
                {loc.mentions} mentions | Sentiment: {loc.avg_sentiment:.2f}
                """)
    else:
        st.info("No geographic data available")

# TAB 5: Analytics
with tab5:
    st.subheader("📈 Advanced Analytics")
    
    col1, col2 = st.columns(2)
    
with col1:
    st.markdown("### 📊 Data Collection Rate")
    
    # Create fresh connection
    temp_db = Database()
    temp_db.connect()
    
    with temp_db.get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                DATE_TRUNC('hour', created_at) as hour,
                COUNT(*) as count
            FROM raw_data
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY DATE_TRUNC('hour', created_at)
            ORDER BY hour
        """)
        hourly_data = cursor.fetchall()
    
    temp_db.disconnect()
    
    if hourly_data:
        df_hourly = pd.DataFrame(hourly_data)
        
        fig = px.line(
            df_hourly,
            x='hour',
            y='count',
            title='Messages per Hour (Last 24h)',
            markers=True
        )
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 ML Anomaly Detection")
        
        # Load from CSV if exists
        try:
            df_anomalies = pd.read_csv('analytics/notebooks/ml_risk_predictions.csv')
            anomaly_count = df_anomalies['is_anomaly'].sum()
            
            st.metric("🚨 Anomalies Detected", anomaly_count)
            
            risk_dist = df_anomalies['risk_level'].value_counts()
            
            fig = px.pie(
                values=risk_dist.values,
                names=risk_dist.index,
                title='Risk Level Distribution',
                color=risk_dist.index,
                color_discrete_map={
                    'LOW': 'green',
                    'MEDIUM': 'orange',
                    'HIGH': 'red'
                }
            )
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        except FileNotFoundError:
            st.info("Run ML notebooks to generate anomaly predictions")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <b>Situational Awareness Platform</b> | ModelX Competition | Built with AI/ML<br>
    🤖 Powered by: DistilBERT (Sentiment) | Isolation Forest (Anomaly Detection)<br>
    📊 Data Sources: Ada Derana, The Island, Social Media Simulation
</div>
""", unsafe_allow_html=True)