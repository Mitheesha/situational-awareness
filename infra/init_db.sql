-- Situational Awareness Platform Database Schema
-- Layer 2 - Permanent Storage & Processing

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Raw collected data table (normalized storage)
CREATE TABLE IF NOT EXISTS raw_data (
    id SERIAL PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    url TEXT,
    title TEXT NOT NULL,
    snippet TEXT,
    published TIMESTAMP,
    fetched_at TIMESTAMP NOT NULL,
    language VARCHAR(10),
    collector VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Social media specific metadata (extracted from JSONB)
CREATE TABLE IF NOT EXISTS social_posts (
    id SERIAL PRIMARY KEY,
    raw_data_id INTEGER REFERENCES raw_data(id),
    topic VARCHAR(255),
    sentiment VARCHAR(50),
    urgency VARCHAR(20),
    location VARCHAR(100),
    username VARCHAR(255),
    user_followers INTEGER,
    retweet_count INTEGER,
    like_count INTEGER,
    is_simulated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processed signals (for analytics - Layer 3)
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    signal_type VARCHAR(100) NOT NULL,
    topic VARCHAR(255),
    description TEXT,
    urgency VARCHAR(20),
    confidence_score FLOAT,
    source_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business insights (final output - Layer 3)
CREATE TABLE IF NOT EXISTS insights (
    id SERIAL PRIMARY KEY,
    insight_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity VARCHAR(20),
    affected_areas TEXT[],
    recommendation TEXT,
    supporting_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP
);

-- Processing statistics (monitoring)
CREATE TABLE IF NOT EXISTS processing_stats (
    id SERIAL PRIMARY KEY,
    batch_id UUID DEFAULT uuid_generate_v4(),
    records_processed INTEGER,
    records_failed INTEGER,
    processing_time_ms INTEGER,
    source_breakdown JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_raw_data_source ON raw_data(source);
CREATE INDEX IF NOT EXISTS idx_raw_data_type ON raw_data(source_type);
CREATE INDEX IF NOT EXISTS idx_raw_data_fetched ON raw_data(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_data_published ON raw_data(published DESC);
CREATE INDEX IF NOT EXISTS idx_raw_data_created ON raw_data(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_social_topic ON social_posts(topic);
CREATE INDEX IF NOT EXISTS idx_social_urgency ON social_posts(urgency);
CREATE INDEX IF NOT EXISTS idx_social_location ON social_posts(location);

CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_topic ON signals(topic);
CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_insights_type ON insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_created ON insights(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_insights_severity ON insights(severity);

-- Useful views
CREATE OR REPLACE VIEW recent_activity AS
SELECT 
    id,
    source,
    source_type,
    title,
    published,
    fetched_at,
    created_at
FROM raw_data
ORDER BY fetched_at DESC
LIMIT 100;

CREATE OR REPLACE VIEW hourly_collection_rate AS
SELECT 
    DATE_TRUNC('hour', fetched_at) as hour,
    source_type,
    COUNT(*) as count
FROM raw_data
GROUP BY DATE_TRUNC('hour', fetched_at), source_type
ORDER BY hour DESC;

CREATE OR REPLACE VIEW social_topic_summary AS
SELECT 
    topic,
    urgency,
    COUNT(*) as mention_count,
    AVG(like_count) as avg_likes,
    AVG(retweet_count) as avg_retweets,
    MAX(sp.created_at) as latest_mention
FROM social_posts sp
WHERE sp.created_at > NOW() - INTERVAL '24 hours'
GROUP BY topic, urgency
ORDER BY mention_count DESC;

CREATE OR REPLACE VIEW source_reliability AS
SELECT 
    source,
    COUNT(*) as total_articles,
    COUNT(DISTINCT DATE(fetched_at)) as active_days,
    MIN(fetched_at) as first_seen,
    MAX(fetched_at) as last_seen
FROM raw_data
WHERE source_type = 'news'
GROUP BY source
ORDER BY total_articles DESC;